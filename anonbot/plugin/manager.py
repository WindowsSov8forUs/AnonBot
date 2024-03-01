'''实现插件的加载、卸载与重载'''

import sys
import pkgutil
import importlib
from pathlib import Path
from itertools import chain
from types import ModuleType
from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder, SourceFileLoader, ModuleSpec
from typing import Iterable, Optional, Sequence

from anonbot.log import logger
from anonbot.utils import path_to_module_name

from .model import Plugin, PluginMetadata
from . import (
    _managers,
    _current_plugin_chain,
    _new_plugin,
    _revert_plugin,
    _module_name_to_plugin_name
)

class PluginManager:
    '''插件管理器'''
    
    def __init__(
        self,
        search_path: Optional[Iterable[str]] = None
    ) -> None:
        self.search_path: set[str] = set(search_path or [])
        
        self._plugin_names: dict[str, str] = {}
        self._searched_plugin_names: dict[str, Path] = {}
        self.prepare_plugins()
    
    def __repr__(self) -> str:
        return f'PluginManager(search_path={self.search_path})'
    
    @property
    def plugins(self) -> set[str]:
        '''返回所有插件名称'''
        return set(self._plugin_names.keys())
    
    @property
    def searched_plugin_names(self) -> set[str]:
        '''返回所有已搜索的插件名称'''
        return set(self._searched_plugin_names.keys())
    
    @property
    def available_plugins(self) -> set[str]:
        '''返回所有可用的插件名称'''
        return self.plugins | self.searched_plugin_names
    
    def _previous_plugins(self) -> set[str]:
        _pre_managers: list[PluginManager]
        if self in _managers:
            _pre_managers = _managers[:_managers.index(self)]
        else:
            _pre_managers = _managers[:]
        
        return {
            *chain.from_iterable(manager.available_plugins for manager in _pre_managers)
        }
    
    def prepare_plugins(self) -> set[str]:
        '''搜索插件并缓存插件名称'''
        previous_plugins = self._previous_plugins()
        searched_plugins: dict[str, Path] = {}
        plugins: dict[str, str] = {}
        
        for plugin in self.plugins:
            name = _module_name_to_plugin_name(plugin)
            if name in plugins or name in previous_plugins:
                raise RuntimeError(
                    f'Plugin already exists: {name}!'
                )
            plugins[name] = plugin
        
        self._plugin_names = plugins
        
        for module_info in pkgutil.iter_modules(self.search_path):
            if module_info.name.startswith('_'):
                continue
            
            if (
                module_info.name in searched_plugins
                or module_info.name in previous_plugins
                or module_info.name in plugins
            ):
                raise RuntimeError(
                    f'Plugin already exists: {module_info.name}!'
                )
            
            if not (
                module_spec := module_info.module_finder.find_spec(
                    module_info.name, None
                )
            ):
                raise RuntimeError(
                    f'Plugin already exists: {module_info.name}!'
                )
            
            if not (
                module_spec := module_info.module_finder.find_spec(
                    module_info.name, None
                )
            ):
                continue
            if not (module_path := module_spec.origin):
                continue
            searched_plugins[module_info.name] = Path(module_path).resolve()
        
        self._searched_plugin_names = searched_plugins
        
        return self.available_plugins
    
    def load_plugin(self, name: str) -> Optional[Plugin]:
        '''加载指定插件'''
        
        try:
            if name in self.plugins:
                module = importlib.import_module(name)
            elif name in self._plugin_names:
                module = importlib.import_module(self._plugin_names[name])
            elif name in self._searched_plugin_names:
                module = importlib.import_module(
                    path_to_module_name(self._searched_plugin_names[name])
                )
            else:
                raise RuntimeError(f'Plugin not found: {name}!')
            
            if (
                plugin := getattr(module, '__plugin__', None)
            ) is None or not isinstance(plugin, Plugin):
                raise RuntimeError(f'Module {module.__name__} is not loaded as a plugin!')
            logger.info(
                f'Succeeded to load plugin {plugin.name} from {plugin.module_name}',
                name='loader'
            )
            return plugin
        except Exception as exception:
            logger.error(
                f'Failed to load plugin {name}: {exception}',
                exception=exception,
                name='loader'
            )
    
    def load_all_plugins(self) -> set[Plugin]:
        '''加载所有可用插件'''
        
        return set(
            filter(None, map(self.load_plugin, self.available_plugins))
        )

class PluginFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[ModuleType] = None
    ) -> Optional[ModuleSpec]:
        if _managers:
            module_spec = PathFinder.find_spec(fullname, path, target)
            if not module_spec:
                return
            module_origin = module_spec.origin
            if not module_origin:
                return
            module_path = Path(module_origin).resolve()
            
            for manager in reversed(_managers):
                if (
                    fullname in manager.plugins
                    or module_path in manager._searched_plugin_names.values()
                ):
                    module_spec.loader = PluginLoader(manager, fullname, module_origin)
                    return module_spec
        
        return

class PluginLoader(SourceFileLoader):
    def __init__(self, manager: PluginManager, fullname: str, path: str) -> None:
        self.manager = manager
        self.loaded = False
        super().__init__(fullname, path)
    
    def create_module(self, spec: ModuleSpec) -> Optional[ModuleType]:
        if self.name in sys.modules:
            self.loaded = True
            return sys.modules[self.name]
        return super().create_module(spec)
    
    def exec_module(self, module: ModuleType) -> None:
        if self.loaded:
            return
        
        plugin = _new_plugin(self.name, module, self.manager)
        setattr(module, '__plugin__', plugin)
        
        parent_plugins = _current_plugin_chain.get()
        for pre_plugin in reversed(parent_plugins):
            if _managers.index(pre_plugin.manager) < _managers.index(self.manager):
                plugin.parent_plugin = pre_plugin
                pre_plugin.sub_plugins.add(plugin)
                break
        
        _plugin_token = _current_plugin_chain.set(parent_plugins + (plugin,))
        
        try:
            super().exec_module(module)
        except Exception:
            _revert_plugin(plugin)
            raise
        finally:
            _current_plugin_chain.reset(_plugin_token)
        
        metadata: Optional[PluginMetadata] = getattr(module, '__plugin_meta__', None)
        plugin.metadata = metadata
        
        return

sys.meta_path.insert(0, PluginFinder())
