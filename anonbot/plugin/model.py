'''插件相关信息'''

from types import ModuleType
from dataclasses import field, dataclass
from typing import TYPE_CHECKING, Any, Type, Optional

from pydantic import BaseModel

from anonbot.processor import Processor

if TYPE_CHECKING:
    from .manager import PluginManager
    
@dataclass(eq=False)
class PluginMetadata:
    '''插件元信息'''
    
    name: str
    '''插件名称'''
    descrition: str
    '''插件功能介绍'''
    usage: str
    '''插件使用方法'''
    config: Optional[Type[BaseModel]] = None
    '''插件配置项'''
    
    extra: dict[Any, Any] = field(default_factory=dict)
    '''额外信息'''

@dataclass(eq=False)
class Plugin:
    '''插件信息'''
    
    name: str
    '''插件索引标识'''
    module: ModuleType
    '''插件模块对象'''
    module_name: str
    '''模块路径'''
    manager: 'PluginManager'
    '''导入该插件的插件管理器'''
    processor: set[Type[Processor]] = field(default_factory=set)
    '''插件加载时定义的 `Processor`'''
    parent_plugin: Optional['Plugin'] = None
    '''父插件'''
    sub_plugins: set['Plugin'] = field(default_factory=set)
    '''子插件集合'''
    metadata: Optional[PluginMetadata] = None
