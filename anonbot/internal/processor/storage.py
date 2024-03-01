import abc
from collections import defaultdict
from typing import TYPE_CHECKING, Type, Mapping, MutableMapping

if TYPE_CHECKING:
    from .processor import Processor

class ProcessorStorage(abc.ABC, MutableMapping[int, list[Type['Processor']]]):
    '''事件处理器存储基类'''
    
    @abc.abstractmethod
    def __init__(self, processors: Mapping[int, list[Type['Processor']]]) -> None:
        raise NotImplementedError

class _DictStorage(defaultdict, ProcessorStorage):
    def __init__(self, processors: Mapping[int, list[Type['Processor']]]) -> None:
        super().__init__(list, processors)

DEFAULT_STORAGE_CLASS = _DictStorage
'''默认的事件处理器存储类'''
