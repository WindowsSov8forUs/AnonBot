import inspect
from typing_extensions import override
from contextlib import ExitStack, contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    Type,
    Tuple,
    Union,
    Literal,
    Callable,
    Optional,
    Annotated,
    cast,
    get_args,
    get_origin
)

from pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo as _PydanticFieldInfo

from anonbot.dependency import Param, Dependent
from anonbot.typing import StateType, HandlerType, DependencyCache
from anonbot.utils import (
    get_name,
    is_gen_callable,
    generic_check_issubclass
)
from anonbot.dependency.utils import (
    FieldInfo,
    ParameterField,
    check_field_type,
    extract_field_info
)

if TYPE_CHECKING:
    from anonbot.processor import Processor
    from anonbot.adapter import Bot, Event

EXTRA_FIELD_INFO = (
    "gt",
    "lt",
    "ge",
    "le",
    "multiple_of",
    "allow_inf_nan",
    "max_digits",
    "decimal_places",
    "min_items",
    "max_items",
    "unique_items",
    "min_length",
    "max_length",
    "regex",
)

class DependsInner:
    def __init__(
        self,
        dependency: Optional[HandlerType] = None,
        *,
        use_cache: bool = True,
        validate: Union[bool, _PydanticFieldInfo] = False
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache
        self.validate = validate
    
    def __repr__(self) -> str:
        dep = get_name(self.dependency)
        cache = '' if self.use_cache else ', use_cache=False'
        validate = f', validate={self.validate}' if self.validate else ''
        return f'DependsInner({dep}{cache}{validate})'

def Depends(
    dependency: Optional[HandlerType] = None,
    *,
    use_cache: bool = True,
    validate: Union[bool, _PydanticFieldInfo] = False
) -> Any:
    '''子依赖装饰器

    参数:
        dependency (Optional[HandlerType]): 依赖处理函数
        use_cache (bool): 是否使用缓存
        validate (Union[bool, FieldInfo]): 是否验证参数
    '''
    return DependsInner(dependency, use_cache=use_cache, validate=validate)

class DependParam(Param):
    '''子依赖注入参数'''
    
    def __init__(self, *args: Any, dependent: Dependent[Any], use_cache: bool, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dependent = dependent
        self.use_cache = use_cache
    
    def __repr__(self) -> str:
        return f'Depends({self.dependent}, use_cache={self.use_cache})'
    
    @classmethod
    def _from_field(
        cls, sub_dependent: Dependent, use_cache: bool, validate: Union[bool, _PydanticFieldInfo]
    ) -> Self:
        kwargs = {}
        if isinstance(validate, FieldInfo):
            kwargs.update(extract_field_info(validate))
        
        kwargs['validate'] = bool(validate)
        kwargs['dependent'] = sub_dependent
        kwargs['use_cache'] = use_cache
        
        return cls(**kwargs)
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Type[Param]]) -> Optional[Self]:
        type_annotation, depends_inner = param.annotation, None
        if get_origin(param.annotation) is Annotated:
            type_annotation, *extra_args = get_args(param.annotation)
            depends_inner = next(
                (x for x in reversed(extra_args) if isinstance(x, DependsInner)), None
            )
        
        depends_inner = (
            param.default if isinstance(param.default, DependsInner) else depends_inner
        )
        if depends_inner is None:
            return
        
        dependency: HandlerType
        if depends_inner.dependency is None:
            assert (
                type_annotation is not inspect.Signature.empty
            ), 'Dependency cannot be empty'
            dependency = type_annotation
        else:
            dependency = depends_inner.dependency
        
        sub_dependent = Dependent[Any].parse(
            call=dependency,
            allow_types=allow_types
        )
        
        return cls._from_field(
            sub_dependent, depends_inner.use_cache, depends_inner.validate
        )
    
    @classmethod
    @override
    def _check_parameterless(cls, value: Any, allow_types: Tuple[Type[Param]]) -> Optional['Param']:
        if isinstance(value, DependsInner):
            assert value.dependency, 'Dependency cannot be empty'
            dependent = Dependent[Any].parse(
                call=value.dependency, allow_types=allow_types
            )
            return cls._from_field(dependent, value.use_cache, value.validate)
    
    @override
    def _solve(
        self,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None,
        **kwargs: Any
    ) -> Any:
        use_cache: bool = self.use_cache
        dependency_cache = {} if dependency_cache is None else dependency_cache
        
        sub_dependent: Dependent = self.dependent
        call = cast(Callable[..., Any], sub_dependent.call)
        
        sub_values = sub_dependent.solve(
            stack=stack,
            dependency_cache=dependency_cache,
            **kwargs
        )
        
        if use_cache and call in dependency_cache:
            return dependency_cache[call]
        elif is_gen_callable(call):
            assert isinstance(stack, ExitStack), 'Generator dependency should be called in context'
            cm = contextmanager(call)(**sub_values)
            dependency_cache[call] = cm
            return cm
        dependency_cache[call] = call(**sub_values)
        return call(**sub_values)
    
    @override
    def _check(self, **kwargs: Any) -> None:
        self.dependent.check(**kwargs)

class BotParam(Param):
    '''`anonbot.adapters.Bot` 注入参数'''
    
    def __init__(self, *args: Any, checker: Optional[ParameterField] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.checker = checker
    
    def __repr__(self) -> str:
        return (
            'BotParam('
            + (
                repr(self.checker.annotation)
                if self.checker is not None
                else ''
            )
            + ')'
        )
    
    @classmethod
    @override
    def _check_param(
        cls, param: inspect.Parameter, allow_types: Tuple[Type[Param], ...]
    ) -> Optional[Self]:
        from anonbot.adapter import Bot
        
        if generic_check_issubclass(param.annotation, Bot):
            checker: Optional[ParameterField] = None
            if param.annotation is not Bot:
                checker = ParameterField.construct(
                    name=param.name,
                    annotation=param.annotation,
                    field_info=FieldInfo()
                )
            return cls(default=Ellipsis, checker=checker)
        elif param.annotation == param.empty and param.name == 'bot':
            return cls(default=Ellipsis)
    
    @override
    def _solve(self, bot: 'Bot', **kwargs: Any) -> Any:
        return bot
    
    @override
    def _check(self, bot: 'Bot', **kwargs: Any) -> None:
        if self.checker is not None:
            check_field_type(self.checker, bot)

class EventParam(Param):
    '''`anonbot.adapters.Event` 注入参数'''
    
    def __init__(self, *args: Any, checker: Optional[ParameterField] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.checker = checker
    
    def __repr__(self) -> str:
        return (
            'EventParam('
            + (
                repr(self.checker.annotation)
                if self.checker is not None
                else ''
            )
            + ')'
        )
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Type[Param], ...]) -> Optional[Self]:
        from anonbot.adapter import Event
        
        if generic_check_issubclass(param.annotation, Event):
            checker: Optional[ParameterField] = None
            if param.annotation is not Event:
                checker = ParameterField.construct(
                    name=param.name,
                    annotation=param.annotation,
                    field_info=FieldInfo()
                )
            return cls(default=Ellipsis, checker=checker)
        elif param.annotation == param.empty and param.name == 'event':
            return cls(default=Ellipsis)
    
    @override
    def _solve(self, event: 'Event', **kwargs: Any) -> Any:
        return event
    
    @override
    def _check(self, event: 'Event', **kwargs: Any) -> None:
        if self.checker is not None:
            check_field_type(self.checker, event)

class StateParam(Param):
    '''事件处理状态注入参数'''
    
    def __repr__(self) -> str:
        return 'StateParam()'
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Type[Param], ...]) -> Optional[Self]:
        if param.annotation is StateType:
            return cls(default=Ellipsis)
        elif param.annotation == param.empty and param.name == 'state':
            return cls(default=Ellipsis)
    
    @override
    def _solve(self, state: StateType, **kwargs: Any) -> Any:
        return state

class ProcessorParam(Param):
    '''事件处理器注入参数'''
    
    def __init__(self, *args: Any, checker: Optional[ParameterField] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.checker = checker
    
    def __repr__(self) -> str:
        return (
            'ProcessorParam('
            + (repr(self.checker.annotation) if self.checker is not None else '')
            + ')'
        )
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Type[Param], ...]) -> Optional[Self]:
        from anonbot.processor import Processor
        
        if generic_check_issubclass(param.annotation, Processor):
            checker: Optional[ParameterField] = None
            if param.annotation is not Processor:
                checker = ParameterField.construct(
                    name=param.name,
                    annotation=param.annotation,
                    field_info=FieldInfo()
                )
            return cls(default=Ellipsis, checker=checker)
        elif param.annotation == param.empty and param.name == 'processor':
            return cls(default=Ellipsis)
    
    @override
    def _solve(self, processor: 'Processor', **kwargs: Any) -> Any:
        return processor
    
    @override
    def _check(self, processor: 'Processor', **kwargs: Any) -> None:
        if self.checker is not None:
            check_field_type(self.checker, processor)

class ArgInner:
    def __init__(
        self, key: Optional[str], type: Literal['message', 'str', 'plaintext']
    ) -> None:
        self.key: Optional[str] = key
        self.type: Literal['message', 'str', 'plaintext'] = type
    
    def __repr__(self) -> str:
        return f'ArgInner(key={self.key!r}, type={self.type!r})'

def Arg(key: Optional[str] = None) -> Any:
    '''参数消息'''
    return ArgInner(key, 'message')

def ArgStr(key: Optional[str] = None) -> str:
    '''参数消息字符串'''
    return ArgInner(key, 'str') # type: ignore

def ArgPlainText(key: Optional[str] = None) -> str:
    '''参数消息纯文本'''
    return ArgInner(key, 'plaintext') # type: ignore

class ArgParam(Param):
    '''Arg 注入参数'''
    
    def __init__(
        self,
        *args: Any,
        key: str,
        type: Literal['message', 'str', 'plaintext'],
        **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.key = key
        self.type = type
    
    def __repr__(self) -> str:
        return f'ArgParam(key={self.key!r}, type={self.type!r})'
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Type[Param], ...]) -> Optional[Self]:
        if isinstance(param.default, ArgInner):
            return cls(key=param.default.key or param.name, type=param.default.type)
        elif get_origin(param.annotation) is Annotated:
            for arg in get_args(param.annotation)[:0:-1]:
                if isinstance(arg, ArgInner):
                    return cls(key=arg.key or param.name, type=arg.type)
    
    def _solve(self, processor: 'Processor', **kwargs: Any) -> Any:
        message = processor.get_arg(self.key)
        if message is None:
            return message
        if self.type == 'message':
            return message
        elif self.type == 'str':
            return str(message)
        else:
            return message.extract_plain_text()

class ExceptionParam(Param):
    '''Exception 异常注入参数'''
    def __repr__(self) -> str:
        return 'ExceptionParam()'
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Param]) -> Optional[Self]:
        if generic_check_issubclass(param.annotation, Exception):
            return cls()
        elif param.annotation == param.empty and param.name == 'exception':
            return cls()
    
    @override
    def _solve(self, exception: Optional[Exception] = None, **kwargs: Any) -> Any:
        return exception

class DefaultParam(Param):
    '''默认值注入参数'''
    
    def __repr__(self) -> str:
        return f'DefaultParam(default={self.default!r})'
    
    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: Tuple[Type[Param], ...]) -> Optional[Self]:
        if param.default != param.empty:
            return cls(param.default)
    
    @override
    def _solve(self, **kwargs: Any) -> Any:
        return PydanticUndefined

__autodoc__ = {
    "DependsInner": False,
    "StateInner": False,
    "ArgInner": False,
}
