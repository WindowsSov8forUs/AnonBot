import abc
from copy import deepcopy
from dataclasses import field, asdict, dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    Type,
    Tuple,
    Union,
    Generic,
    TypeVar,
    Callable,
    Iterable,
    KeysView,
    Optional,
    Generator,
    ItemsView,
    ValuesView,
    SupportsIndex,
    overload
)

from pydantic import TypeAdapter

from anonbot.utils import custom_validation

if TYPE_CHECKING:
    from .uni import Message as UniMessage

TMS = TypeVar('TMS', bound='MessageSegment')
TM = TypeVar('TM', bound='Message')

@dataclass
class MessageSegment(abc.ABC, Generic[TM]):
    '''消息段基类'''
    type: str
    '''消息段类型'''
    data: dict[str, Any] = field(default_factory=dict)
    '''消息段数据'''
    
    @classmethod
    @abc.abstractmethod
    def get_message_class(cls) -> Type[TM]:
        '''获取消息数组类型'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def __str__(self) -> str:
        '''该消息段所代表的 str，在命令匹配部分使用'''
        raise NotImplementedError
    
    def __len__(self) -> int:
        return len(str(self))
    
    def __ne__(self, other: Self) -> bool:
        return not self == other
    
    def __add__(self: TMS, other: Union[str, TMS, Iterable[TMS]]) -> TM:
        return self.get_message_class()(self) + other
    
    def __radd__(self: TMS, other: Union[str, TMS, Iterable[TMS]]) -> TM:
        return self.get_message_class()(other) + self
    
    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Self], None, None]:
        yield cls._validate
    
    @classmethod
    def _validate(cls, value: Any) -> Self:
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ValueError(f'Expected dict for MessageSegment, got {type(value)}')
        if 'type' not in value:
            raise ValueError(f'Expected dict with \'type\' for MessageSegment, got {value}')
        return cls(type=value['type'], data=value.get('data', {}))
    
    def get(self, key: str, default: Any=None) -> Any:
        return self.data.get(key, default)
    
    def keys(self) -> KeysView[Any]:
        return asdict(self).keys()
    
    def values(self) -> ValuesView[Any]:
        return asdict(self).values()
    
    def items(self) -> ItemsView[str, Any]:
        return asdict(self).items()
    
    def join(self: TMS, iterable: Iterable[Union[TMS, TM]]) -> TM:
        return self.get_message_class()(self).join(iterable)
    
    def copy(self) -> Self:
        return deepcopy(self)
    
    @abc.abstractmethod
    def is_text(self) -> bool:
        '''当前消息段是否为纯文本'''
        raise NotImplementedError

@custom_validation
class Message(list[TMS], abc.ABC):
    '''消息序列

    参数:
        message (str | None | Iterable[TMS] | TMS, optional): 消息内容'''
    def __init__(self, message: Optional[Union[str, TMS, Iterable[TMS]]] = None) -> None:
        super().__init__()
        if message is None:
            return
        elif isinstance(message, str):
            self.extend(self._construct(message))
        elif isinstance(message, MessageSegment):
            self.append(message)
        elif isinstance(message, Iterable):
            self.extend(message)
        else:
            self.extend(self._construct(message))
    
    @classmethod
    @abc.abstractmethod
    def get_segment_class(cls) -> Type[TMS]:
        '''获取消息段类型'''
        raise NotImplementedError
    
    def __str__(self) -> str:
        return ''.join(map(str, self))
    
    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Self], None, None]:
        yield cls._validate
    
    @classmethod
    def _validate(cls, value: Any) -> Self:
        if isinstance(value, cls):
            return value
        elif isinstance(value, Message):
            raise ValueError(f'Type {type(value)} can not be converted to {cls}')
        elif isinstance(value, str):
            pass
        elif isinstance(value, dict):
            value = TypeAdapter(cls.get_segment_class()).validate_python(value)
        elif isinstance(value, Iterable):
            value = [TypeAdapter(cls.get_segment_class()).validate_python(v) for v in value]
        else:
            raise ValueError(f'Message need str, dict or Iterable for value, not {type(value)}')
        return cls(value)
    
    @staticmethod
    @abc.abstractmethod
    def _construct(message: str) -> Iterable[TMS]:
        '''构造消息数组'''
        raise NotImplementedError
    
    def __add__(self, other: str | TMS | Iterable[TMS]) -> Self:
        result = self.copy()
        result += other
        return result
    
    def __radd__(self, other: str | TMS | Iterable[TMS]) -> Self:
        result = self.__class__(other)
        return result + self
    
    def __iadd__(self, other: str | TMS | Iterable[TMS]) -> Self:
        if isinstance(other, str):
            self.extend(self._construct(other))
        elif isinstance(other, MessageSegment):
            self.append(other)
        elif isinstance(other, Iterable):
            self.extend(other)
        else:
            raise TypeError(f'Unsupported type {type(other)!r}')
        return self
    
    @overload
    def __getitem__(self, args: str) -> Self:
        '''获取仅包含指定消息段类型的消息

        参数:
            args (str): 消息段类型

        返回:
            Self: 所有类型为 `args` 的消息段
        '''
        ...
    
    @overload
    def __getitem__(self, args: Tuple[str, int]) -> TMS:
        '''索引指定类型的消息段

        参数:
            args (str, int): 消息段类型和索引

        返回:
            TMS: 类型为 `args[0]` 的消息段第 `args[1]` 个
        '''
        ...
    
    @overload
    def __getitem__(self, args: Tuple[str, slice]) -> Self:
        '''切片指定类型的消息段

        参数:
            args (str, slice): 消息段类型和切片

        返回:
            Self: 类型为 `args[0]` 的消息段切片 `args[1]`
        '''
        ...
    
    @overload
    def __getitem__(self, args: int) -> TMS:
        '''索引消息段

        参数:
            args (int): 索引

        返回:
            TMS: 第 `args` 个消息段
        '''
        ...
    
    @overload
    def __getitem__(self, args: slice) -> Self:
        '''切片消息段

        参数:
            args (slice): 切片

        返回:
            Self: 消息切片 `args`
        '''
        ...
    
    def __getitem__(
        self,
        args: Union[
            str,
            Tuple[str, int],
            Tuple[str, slice],
            int,
            slice,
        ],
    ) -> Union[TMS, Self]:
        arg1, arg2 = args if isinstance(args, tuple) else (args, None)
        if isinstance(arg1, int) and arg2 is None:
            return super().__getitem__(arg1)
        elif isinstance(arg1, slice) and arg2 is None:
            return self.__class__(super().__getitem__(arg1))
        elif isinstance(arg1, str) and arg2 is None:
            return self.__class__(filter(lambda x: x.type == arg1, self))
        elif isinstance(arg1, str) and isinstance(arg2, int):
            return [seg for seg in self if seg.type == arg1][arg2]
        elif isinstance(arg1, str) and isinstance(arg2, slice):
            return self.__class__([seg for seg in self if seg.type == arg1][arg2])
        else:
            raise ValueError('Incorrect arguments to slice')
    
    def __contains__(self, value: TMS | str) -> bool:
        '''检查消息段是否存在

        参数:
            value (TMS | str): 消息段或消息段类型

        返回:
            bool: 消息内是否存在给定消息段或给定类型的消息段
        '''
        if isinstance(value, str):
            return bool(next(filter(lambda x: x.type == value, self), None))
        return super().__contains__(value)
    
    def has(self, value: Union[TMS, str]) -> bool:
        '''检查消息段是否存在

        参数:
            value (TMS | str): 消息段或消息段类型

        返回:
            bool: 消息内是否存在给定消息段或给定类型的消息段
        '''
        return value in self
    
    def index(self, value: Union[TMS, str], *args: SupportsIndex) -> int:
        '''索引消息段

        参数:
            value (TMS | str): 消息段或者消息段类型
            arg (SupportsIndex): start 与 end

        返回:
            int: 索引 index
        '''
        if isinstance(value, str):
            first_segment = next(filter(lambda x: x.type == value, self), None)
            if first_segment is None:
                raise ValueError(f'Type {value} not found in message')
            return super().index(first_segment, *args)
        return super().index(value, *args)
    
    def get(self, type_: str, count: Optional[int] = None) -> Self:
        '''获取指定类型的消息段

        参数:
            type_ (str): 消息段类型
            count (int, optional): 获取个数

        返回:
            Self: 构建的新消息
        '''
        if count is None:
            return self[type_]
        
        iterator, filtered = filter(lambda x: x.type == type_, self), self.__class__()
        for _ in range(count):
            seg = next(iterator, None)
            if seg is None:
                break
            filtered.append(seg)
        return filtered
    
    def count(self, value: Union[TMS, str]) -> int:
        '''计算指定消息段的个数

        参数:
            value (TMS | str): 消息段或者消息段类型

        返回:
            int: 个数
        '''
        return len(self[value]) if isinstance(value, str) else super().count(value)
    
    def only(self, value: Union[TMS, str]) -> bool:
        '''检查消息是否仅包含指定消息段

        参数:
            value (TMS | str): 消息段或者消息段类型

        返回:
            bool: 是否仅包含指定消息段
        '''
        if isinstance(value, str):
            return all(seg.type == value for seg in self)
        return all(seg == value for seg in self)
    
    def append(self, obj: Union[str, TMS]) -> Self:
        '''添加一个消息段到消息数组末尾。

        参数:
            obj (str | TMS): 要添加的消息段
        '''
        if isinstance(obj, MessageSegment):
            super().append(obj)
        elif isinstance(obj, str):
            self.extend(self._construct(obj))
        else:
            raise ValueError(f'Unexpected type: {type(obj)} {obj}')
        return self
    
    def extend(self, obj: Union[Self, Iterable[TMS]]) -> Self:
        '''拼接一个消息数组或多个消息段到消息数组末尾。

        参数:
            obj (Self | Iterable[TMS]): 要添加的消息数组
        '''
        for segment in obj:
            self.append(segment)
        return self
    
    def join(self, iterable: Iterable[Union[TMS, Self]]) -> Self:
        '''将多个消息连接并将自身作为分割

        参数:
            iterable (Iterable[TMS | Self]): 要连接的消息

        返回:
            Self: 连接后的消息
        '''
        ret = self.__class__()
        for index, message in enumerate(iterable):
            if index != 0:
                ret.extend(self)
            if isinstance(message, MessageSegment):
                ret.append(message.copy())
            else:
                ret.extend(message.copy())
        return ret
    
    def copy(self) -> Self:
        '''深拷贝消息'''
        return deepcopy(self)
    
    def include(self, *types: str) -> Self:
        '''过滤消息

        参数:
            types (str): 包含的消息段类型

        返回:
            Self: 新构造的消息
        '''
        return self.__class__(filter(lambda x: x.type in types, self))
    
    def exclude(self, *types: str) -> Self:
        '''过滤消息

        参数:
            types (str): 不包含的消息段类型

        返回:
            Self: 新构造的消息
        '''
        return self.__class__(filter(lambda x: x.type not in types, self))
    
    def extract_plain_text(self) -> str:
        '''提取消息内纯文本消息'''
        return ''.join(map(str, filter(lambda x: x.is_text(), self)))

    @staticmethod
    @abc.abstractmethod
    def parse_uni_message(uni_message: 'UniMessage') -> Iterable[TMS]:
        '''解析 uni 消息

        参数:
            uni_message (uni.Message): uni 消息

        返回:
            Iterable[TMS]: 解析后的消息
        '''
        raise NotImplementedError
