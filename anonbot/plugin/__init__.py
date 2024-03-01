'''AnonBot 插件编写便携工具'''

from itertools import chain
from types import ModuleType
from typing import Tuple, Optional
from contextvars import ContextVar

_plugins: dict[str, 'Plugin'] = {}
_managers: list['PluginManager'] = []
_current_plugin_chain: ContextVar[Tuple['Plugin', ...]] = ContextVar(
    '_current_plugin_chain', default=()
)
_plugin_load_chain: ContextVar[Tuple['Plugin', ...]] = ContextVar(
    '_plugin_load_chain', default=()
)

def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.rsplit('.', 1)[-1]

def _new_plugin(
    module_name: str, module: ModuleType, manager: 'PluginManager'
) -> 'Plugin':
    plugin_name = _module_name_to_plugin_name(module_name)
    if plugin_name in _plugins:
        raise RuntimeError('Plugin already exists!')
    plugin = Plugin(plugin_name, module, module_name, manager)
    _plugins[plugin_name] = plugin
    return plugin

def _revert_plugin(plugin: 'Plugin') -> None:
    if plugin.name not in _plugins:
        raise RuntimeError('Plugin not found!')
    del _plugins[plugin.name]
    for parent_plugin in plugin.parent_plugins:
        parent_plugin.child_plugins.remove(plugin)

def get_plugin(name: str) -> Optional['Plugin']:
    '''获取已经导入的某个插件'''
    return _plugins.get(name)

def get_plugin_by_module_name(module_name: str) -> Optional['Plugin']:
    '''通过模块名获取已经导入的插件'''
    loaded = {plugin.module_name: plugin for plugin in _plugins.values()}
    has_parent = True
    while has_parent:
        if module_name in loaded:
            return loaded[module_name]
        module_name, *has_parent = module_name.rsplit('.', 1)

def get_loaded_plugins() -> set['Plugin']:
    '''获取已经导入的插件'''
    return set(_plugins.values())

def get_available_plugins() -> set[str]:
    '''获取可用的插件名称'''
    return {*chain.from_iterable(manager.available_plugins for manager in _managers)}

from .on import on as on
from .manager import PluginManager
from .on import on_type as on_type
from .model import Plugin as Plugin
from .on import on_regex as on_regex
from .load import require as require
from .on import on_command as on_command
from .on import on_keyword as on_keyword
from .on import on_endswith as on_endswith
from .on import on_internal as on_internal
from .on import on_fullmatch as on_fullmatch
from .load import load_plugin as load_plugin
from .on import on_startswith as on_startswith
from .load import load_plugins as load_plugins
from .on import on_guild_added as on_guild_added
from .on import on_login_added as on_login_added
from .model import PluginMetadata as PluginMetadata
from .on import on_guild_removed as on_guild_removed
from .on import on_guild_request as on_guild_request
from .on import on_login_removed as on_login_removed
from .on import on_login_updated as on_login_updated
from .on import on_friend_request as on_friend_request
from .on import on_reaction_added as on_reaction_added
from .on import on_message_created as on_message_created
from .on import on_message_deleted as on_message_deleted
from .on import on_message_updated as on_message_updated
from .on import on_reaction_removed as on_reaction_removed
from .on import on_guild_member_added as on_guild_member_added
from .on import on_guild_role_created as on_guild_role_created
from .on import on_guild_role_deleted as on_guild_role_deleted
from .on import on_guild_role_updated as on_guild_role_updated
from .on import on_interaction_button as on_interaction_button
from .on import on_interaction_command as on_interaction_command
from .on import on_guild_member_removed as on_guild_member_removed
from .on import on_guild_member_request as on_guild_member_request
from .on import on_guild_member_updated as on_guild_member_updated
