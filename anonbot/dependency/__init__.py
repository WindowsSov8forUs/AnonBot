'''AnonBot 对依赖注入的定义与处理的实现'''

import abc
import inspect
from dataclasses import field, dataclass
from typing import (
    Any,
    Type,
    Tuple,
    Generic,
    TypeVar,
    Callable,
    Iterable,
    Optional,
    cast
)

from anonbot.log import logger
from anonbot.threading import Task, gather
from anonbot.typing import _DependentCallable
from anonbot.exception import SkippedException

from .utils import (
    PydanticUndefined,
    FieldInfo,
    ParameterField,
    check_field_type,
    get_typed_signature
)

R = TypeVar('R')
T = TypeVar('T', bound='Dependent')

class Param(abc.ABC, FieldInfo):
    '''依赖注入参数单元'''
    
    def __init__(self, *args, validate: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.validate = validate
        '''是否需要验证参数'''
    
    @classmethod
    def _check_param(
        cls, param: inspect.Parameter, allow_types: Tuple[Type['Param'], ...]
    ) -> Optional['Param']:
        return
    
    @classmethod
    def _check_parameterless(
        cls, value: Any, allow_types: Tuple[Type['Param'], ...]
    ) -> Optional['Param']:
        return
    
    @abc.abstractmethod
    def _solve(self, **kwargs: Any) -> Any:
        raise NotImplementedError
    
    def _check(self, **kwargs: Any) -> None:
        return

@dataclass(frozen=True)
class Dependent(Generic[R]):
    '''依赖注入容器'''
    
    call: _DependentCallable[R]
    params: Tuple[ParameterField, ...] = field(default_factory=tuple)
    parameterless: Tuple[Param, ...] = field(default_factory=tuple)
    
    def __repr__(self) -> str:
        if inspect.isfunction(self.call) or inspect.isclass(self.call):
            call_str = self.call.__name__
        else:
            call_str = repr(self.call)
        return (
            f'Dependent(call={call_str}'
            + (f', parameterless={self.parameterless}' if self.parameterless else '')
            + ')'
        )
    
    def __call__(self, **kwargs: Any) -> R:
        try:
            self.check(**kwargs)
            
            values = self.solve(**kwargs)
            return cast(Callable[..., R], self.call)(**values)
        except SkippedException as e:
            logger.trace(f'Skipped {self} with {e}')
            raise
    
    @staticmethod
    def parse_params(
        call: _DependentCallable[R], allow_types: Tuple[Type[Param], ...]
    ):
        fields: list[ParameterField] = []
        params = get_typed_signature(call).parameters.values()
        
        for param in params:
            if isinstance(param.default, Param):
                field_info = param.default
            else:
                for allow_type in allow_types:
                    if field_info := allow_type._check_param(param, allow_types):
                        break
                else:
                    raise ValueError(
                        f'Unknown parameter {param.name} '
                        f'for function {call} with type {param.annotation}'
                    )
            
            annotation: Any = Any
            if param.annotation is not param.empty:
                annotation = param.annotation

            fields.append(
                ParameterField.construct(
                    name=param.name,
                    annotation=annotation,
                    field_info=field_info
                )
            )
        
        return tuple(fields)
    
    @staticmethod
    def parse_parameterless(
        parameterless: Tuple[Any, ...], allow_types: Tuple[Type[Param], ...]
    ) -> Tuple[Param, ...]:
        parameterless_params: list[Param] = []
        for value in parameterless:
            for allow_type in allow_types:
                if param := allow_type._check_parameterless(value, allow_types):
                    break
            else:
                raise ValueError(f'Unknown parameterless {value}')
            parameterless_params.append(param)
        return tuple(parameterless_params)
    
    @classmethod
    def parse(
        cls,
        *,
        call: _DependentCallable[R],
        parameterless: Optional[Iterable[Any]] = None,
        allow_types: Iterable[Type[Param]]
    ) -> 'Dependent[R]':
        allow_types = tuple(allow_types)
        
        params = cls.parse_params(call, allow_types)
        parameterless_params = (
            () if parameterless is None
            else cls.parse_parameterless(tuple(parameterless), allow_types)
        )
        
        return cls(call, params, parameterless_params)
    
    def check(self, **params: Any) -> None:
        gather(*(Task(param._check, **params) for param in self.parameterless))
        gather(*(Task(cast(Param, param.field_info)._check, **params) for param in self.params))
    
    def _solve_field(self, field: ParameterField, params: dict[str, Any]) -> Any:
        param = cast(Param, field.field_info)
        value = param._solve(**params)
        if value is PydanticUndefined:
            value = field.get_default()
        v = check_field_type(field, value)
        return v if param.validate else value
    
    def solve(self, **params: Any) -> dict[str, Any]:
        for param in self.parameterless:
            param._solve(**params)
        
        values = gather(*(Task(self._solve_field, field, params) for field in self.params))
        return {field.name: value for field, value in zip(self.params, values)}
