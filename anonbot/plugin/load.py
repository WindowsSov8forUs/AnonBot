'''插件加载接口'''

from pathlib import Path
from types import ModuleType
from typing import Union, Iterable, Optional

from anonbot.utils import path_to_module_name

from .model import Plugin
from .manager import PluginManager
from . import _managers, _current_plugin_chain, get_plugin, _module_name_to_plugin_name

def load_plugin(module_path: Union[str, Path]) -> Optional[Plugin]:
    '''加载单个插件'''
    module_path = (
        path_to_module_name(module_path) if isinstance(module_path, Path)
        else module_path
    )
    manager = PluginManager([module_path])
    _managers.append(manager)
    return manager.load_plugin(module_path)

def load_plugins(*plugin_dir: str) -> set[Plugin]:
    '''导入文件夹下多个插件

    参数:
        plugin_dir (str): 插件文件夹路径
    '''
    manager = PluginManager(search_path=plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()

def _find_manager_by_name(name: str) -> Optional[PluginManager]:
    for manager in reversed(_managers):
        if name in manager.plugins or name in manager.searched_plugin_names:
            return manager
