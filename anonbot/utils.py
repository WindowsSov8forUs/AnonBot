'''AnonBot 的一些工具函数'''

import inspect
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Type,
    Tuple,
    Union,
    Generic,
    Literal,
    TypeVar,
    Callable,
    Optional,
    Protocol,
    Generator,
    get_args,
    overload,
    get_origin
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
    class _CustomValidationClass(Protocol):
        @classmethod
        def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
            ...
    
    CVC = TypeVar('CVC', bound=_CustomValidationClass)

T = TypeVar('T')
R = TypeVar('R')

def is_union(cls: Any) -> bool:
    '''判断是否是 Union 类型'''
    return getattr(cls, '__origin__', None) is Union

def is_none_type(cls: Any) -> bool:
    '''判断是否是 None 类型'''
    return cls is type(None)

def is_literal_type(cls: Any) -> bool:
    '''判断是否是 Literal 类型'''
    return getattr(cls, '__origin__', None) is Literal

def all_literal_values(cls: Any) -> Any:
    '''获取所有 Literal 类型的值'''
    if is_literal_type(cls):
        return cls.__args__
    return None

def generic_check_issubclass(
    cls: Any, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...]]
) -> bool:
    '''检查是否为一个类型子类'''
    
    try:
        return issubclass(cls, class_or_tuple)
    except TypeError:
        origin = get_origin(cls)
        if is_union(origin):
            return all(
                is_none_type(type_) or generic_check_issubclass(type_, class_or_tuple)
                for type_ in get_args(cls)
            )
        elif is_literal_type(cls):
            return all(
                is_none_type(value) or isinstance(value, class_or_tuple)
                for value in all_literal_values(cls)
            )
        
        elif origin:
            try:
                return issubclass(origin, class_or_tuple)
            except TypeError:
                return False
        elif isinstance(cls, TypeVar):
            if cls.__constraints__:
                return all(
                    is_none_type(type_)
                    or generic_check_issubclass(type_, class_or_tuple)
                    for type_ in cls.__constraints__
                )
            elif cls.__bound__:
                return generic_check_issubclass(cls.__bound__, class_or_tuple)
        return False

def is_gen_callable(call: Callable[..., Any]) -> bool:
    '''判断是否是生成器函数'''
    if inspect.isgeneratorfunction(call):
        return True
    func_ = getattr(call, '__func__', None)
    return inspect.isgeneratorfunction(func_)

@overload
def run_with_catch(
    call: Callable[..., T],
    exc: Tuple[Type[Exception], ...],
    return_on_err: None = None,
    *args: Any,
    **kwargs: Any
) -> Union[T, None]:
    ...

@overload
def run_with_catch(
    call: Callable[..., T],
    exc: Tuple[Type[Exception], ...],
    return_on_err: R,
    *args: Any,
    **kwargs: Any
) -> Union[T, R]:
    ...

def run_with_catch(
    call: Callable[..., T],
    exc: Tuple[Type[Exception], ...],
    return_on_err: Optional[R] = None,
    *args: Any,
    **kwargs: Any
) -> Optional[Union[T, R]]:
    '''运行函数并当遇到指定异常时返回指定值'''
    try:
        return call(*args, **kwargs)
    except exc:
        return return_on_err

def get_name(obj: Any) -> str:
    '''获取对象名称'''
    if inspect.isfunction(obj) or inspect.isclass(obj):
        return obj.__name__
    return obj.__class__.__name__

def path_to_module_name(path: Path) -> str:
    '''转换路径为模块名'''
    rel_path = path.resolve().relative_to(Path.cwd().resolve())
    if rel_path.stem == '__init__':
        return '.'.join(rel_path.parts[:-1])
    else:
        return '.'.join(rel_path.parts[:-1] + (rel_path.stem,))

def __get_pydantic_core_schema__(
    cls: Type['_CustomValidationClass'],
    source_type: Any,
    handler: GetCoreSchemaHandler
) -> CoreSchema:
    validators = list(cls.__get_validators__())
    if len(validators) == 1:
        return core_schema.no_info_plain_validator_function(validators[0])
    return core_schema.chain_schema(
        [core_schema.no_info_plain_validator_function(validator) for validator in validators]
    )

def custom_validation(class_: Type['CVC']) -> Type['CVC']:
    setattr(
        class_,
        '__get_pydantic_core_schema__',
        classmethod(__get_pydantic_core_schema__)
    )
    return class_

class classproperty(Generic[T]):
    '''类属性装饰器'''
    
    def __init__(self, func: Callable[[Any], T]) -> None:
        self.func = func
    
    def __get__(self, instance: Any, owner: Optional[Type[Any]] = None) -> T:
        return self.func(type(instance) if owner is None else owner)
