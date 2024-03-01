from typing import (
    TYPE_CHECKING,
    Type,
    Tuple,
    Union,
    TypeVar,
    Iterator,
    KeysView,
    Optional,
    ItemsView,
    ValuesView,
    MutableMapping,
    overload
)

from .storage import DEFAULT_STORAGE_CLASS, ProcessorStorage

if TYPE_CHECKING:
    from .processor import Processor

T = TypeVar('T')

class ProcessorManager(MutableMapping[int, list[Type['Processor']]]):
    '''事件处理器管理器'''
    
    def __init__(self) -> None:
        self.storage: ProcessorStorage = DEFAULT_STORAGE_CLASS({})
    
    def __repr__(self) -> str:
        return f'ProcessorManager(storage={self.storage!r})'
    
    def __contains__(self, obj: object) -> bool:
        return obj in self.storage
    
    def __iter__(self) -> Iterator[int]:
        return iter(self.storage)
    
    def __len__(self) -> int:
        return len(self.storage)
    
    def __getitem__(self, key: int) -> list[Type['Processor']]:
        return self.storage[key]
    
    def __setitem__(self, key: int, value: list[Type['Processor']]) -> None:
        self.storage[key] = value
    
    def __delitem__(self, key: int) -> None:
        del self.storage[key]
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, ProcessorManager) and self.storage == other.storage
    
    def keys(self) -> KeysView[int]:
        return self.storage.keys()
    
    def values(self) -> ValuesView[list[Type['Processor']]]:
        return self.storage.values()
    
    def items(self) -> ItemsView[int, list[Type['Processor']]]:
        return self.storage.items()
    
    @overload
    def get(self, key: int) -> Optional[list[Type['Processor']]]:
        ...
    
    @overload
    def get(self, key: int, default: T) -> Union[list[Type['Processor']], T]:
        ...
    
    def get(self, key: int, default: Optional[T] = None) -> Optional[Union[list[Type['Processor']], T]]:
        return self.storage.get(key, default)
    
    def pop(self, key: int) -> list[Type['Processor']]:
        return self.storage.pop(key)
    
    def popitem(self) -> Tuple[int, list[Type['Processor']]]:
        return self.storage.popitem()
    
    def clear(self) -> None:
        self.storage.clear()
    
    def update(self, __m: MutableMapping[int, list[Type['Processor']]]) -> None:
        self.storage.update(__m)
    
    def setdefault(
        self, key: int, default: list[Type['Processor']]
    ) -> list[Type['Processor']]:
        return self.storage.setdefault(key, default)
    
    def set_storage(self, storage_class: Type[ProcessorStorage]) -> None:
        '''设置事件处理器存储类'''
        self.storage = storage_class(self.storage)
