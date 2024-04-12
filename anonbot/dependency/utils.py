import inspect
from contextlib import suppress
from dataclasses import dataclass, is_dataclass
from typing import (
    Any,
    Self,
    Type,
    Callable,
    Optional,
    Annotated,
    ForwardRef,
    get_args,
    get_origin,
    is_typeddict
)

from pydantic._internal._repr import display_as_type
from pydantic.fields import FieldInfo as BaseFieldInfo
from pydantic import BaseModel, ConfigDict, TypeAdapter
from pydantic_core import PydanticUndefined as PydanticUndefined

from anonbot.log import logger
from anonbot.exception import TypeMisMatch

DEFAULT_CONFIG = ConfigDict(extra='allow', arbitrary_types_allowed=True)

def origin_is_annotated(origin: Optional[Type[Any]]) -> bool:
    with suppress(TypeError):
        return origin is not None and issubclass(origin, Annotated)
    return False

class FieldInfo(BaseFieldInfo):
    def __init__(self, default: Any = PydanticUndefined, **kwargs: Any) -> None:
        super().__init__(default=default, **kwargs)
    
    @property
    def extra(self) -> dict[str, Any]:
        slots = super().__slots__
        return {k: v for k, v in self._attributes_set.items() if k not in slots}

@dataclass
class ParameterField:
    '''参数字段'''
    
    name: str
    annotation: Any
    field_info: FieldInfo
    
    @classmethod
    def _construct(cls, name: str, annotation: Any, field_info: FieldInfo) -> Self:
        return cls(name, annotation, field_info)
    
    @classmethod
    def construct(
        cls, name: str, annotation: Any, field_info: Optional[FieldInfo] = None
    ) -> Self:
        return cls._construct(name, annotation, field_info or FieldInfo())
    
    def _annotation_has_config(self) -> bool:
        type_is_annotated = origin_is_annotated(get_origin(self.annotation))
        inner_type = (
            get_args(self.annotation)[0] if type_is_annotated
            else self.annotation
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
        return display_as_type(self.annotation)
    
    def __hash__(self) -> int:
        return id(self)
    
    def get_default(self) -> Any:
        return self.field_info.get_default(call_default_factory=True)

def extract_field_info(field_info: BaseFieldInfo) -> dict[str, Any]:
    kwargs = field_info._attributes_set.copy()
    kwargs['annotation'] = field_info.rebuild_annotation()
    return kwargs

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
        _type: Any = Annotated[field.annotation, field.field_info]
        return TypeAdapter(_type, config=None if field._annotation_has_config() else DEFAULT_CONFIG).validate_python(value)
    except ValueError:
        raise TypeMisMatch(field, value)
