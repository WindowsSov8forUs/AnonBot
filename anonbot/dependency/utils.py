import inspect
from traceback import format_exception
from contextlib import suppress
from dataclasses import dataclass, is_dataclass
from typing import (
    Any,
    Type,
    Callable,
    Optional,
    Annotated,
    ForwardRef,
    get_args,
    get_origin,
    is_typeddict
)

from pydantic.fields import FieldInfo
from pydantic._internal._repr import display_as_type
from pydantic import BaseModel, ConfigDict, TypeAdapter, create_model

from anonbot.log import logger
from anonbot.exception import TypeMisMatch

def origin_is_annotated(origin: Optional[Type[Any]]) -> bool:
    with suppress(TypeError):
        return origin is not None and issubclass(origin, Annotated)
    return False

@dataclass
class ParameterField:
    '''参数字段'''
    
    name: str
    type_: Any
    field_info: FieldInfo
    
    def __init__(
        self,
        name: str,
        type_: Type[Any],
        field_info: Optional[FieldInfo] = None
    ) -> None:
        self.name = name
        self.type_ = type_
        self.field_info = field_info or FieldInfo()
    
    def _annotation_has_config(self) -> bool:
        type_is_annotated = origin_is_annotated(get_origin(self.type_))
        inner_type = (
            get_args(self.type_)[0] if type_is_annotated
            else self.type_
        )
        try:
            return (
                issubclass(inner_type, BaseModel)
                or is_dataclass(inner_type)
                or is_typeddict(inner_type)
            )
        except TypeError:
            return False
    
    def _type_display(self) -> str:
        return display_as_type(self.type_)
    
    def __hash__(self) -> int:
        return id(self)
    
    def get_default(self) -> Any:
        return self.field_info.get_default(call_default_factory=True)

def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    '''获取可调用对象签名'''
    
    signature = inspect.signature(call)
    globalns = getattr(call, '__globals__', {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_typed_annotation(param, globalns)
        )
        for param in signature.parameters.values()
    ]
    return inspect.Signature(typed_params)

def get_typed_annotation(param: inspect.Parameter, globalns: dict[str, Any]) -> Any:
    """获取参数的类型注解"""

    annotation = param.annotation
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        try:
            annotation = annotation._evaluate(globalns, globalns, frozenset())
        except Exception as e:
            logger.warn(
                f'Unknown ForwardRef["{param.annotation}"] for parameter {param.name}'
            )
            return inspect.Parameter.empty
    return annotation

def check_field_type(field: ParameterField, value: Any) -> Any:
    '''检查字段类型是否匹配'''
    
    try:
        type_: Any = Annotated[field.type_, field.field_info]
        return TypeAdapter(type_).validate_python(value)
    except:
        raise TypeMisMatch(field, value)
