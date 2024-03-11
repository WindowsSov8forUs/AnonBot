'''插件加载接口'''

from pathlib import Path
from types import ModuleType
from typing import Union, Optional

from anonbot.utils import path_to_module_name

from .model import Plugin
from .manager import PluginManager
from . import _managers, _plugin_load_chain, _current_plugin_chain, get_plugin, _module_name_to_plugin_name

def load_plugin(module_path: Union[str, Path]) -> Optional[Plugin]:
    '''加载单个插件'''
    module_path = (
        path_to_module_name(module_path) if isinstance(module_path, Path)
        else module_path
    )
    manager = PluginManager([module_path.split('.')[0]])
    print(manager)
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

def require(*names: str) -> list[ModuleType]:
    '''获取多个插件的导出内容

    传入要导入的插件的名称

    参数:
        names (str): 插件名称

    异常:
        ImportError: 插件无法加载
    '''
    _modules: list[ModuleType] = []
    _plugins: list[Plugin] = []
    for name in names:
        plugin = get_plugin(_module_name_to_plugin_name(name))
        if not plugin:
            if manager := _find_manager_by_name(name):
                plugin = manager.load_plugin(name)
            else:
                _t = _current_plugin_chain.set(())
                try:
                        plugin = load_plugin(name)
                finally:
                    _current_plugin_chain.reset(_t)
        if not plugin:
            raise ImportError(f'Plugin {name!r} cannot be loaded')
        _modules.append(plugin.module)
        _plugins.append(plugin)
    _plugin_load_chain.set(_plugin_load_chain.get() + tuple(_plugins))
    return _modules
