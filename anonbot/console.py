'''AnonBot 控制台控制模块

此模块包含了通过控制台控制 AnonBot 的相关函数，如插件管理等
'''

import sys
import signal
import importlib
from pkgutil import iter_modules
from typing import TYPE_CHECKING, Optional

from anonbot.log import logger
from anonbot.rule import TrieRule, CommandRule
from anonbot.threading import Task, loop, create_task
from anonbot.plugin.load import _find_manager_by_name
from anonbot.plugin import (
    _current_plugin_chain,
    get_plugin,
    load_plugin,
    _revert_plugin,
    get_loaded_plugins,
    _module_name_to_plugin_name
)

if TYPE_CHECKING:
    from anonbot.driver.general import Driver

_driver: Optional['Driver'] = None

def _unload_plugin(name: str) -> None:
    '''卸载插件

    参数:
        name (str): 插件名称
    '''
    plugin = get_plugin(name)
    if plugin is None:
        logger.warn(f'Plugin {name} not found', name='console')
        return
    if not plugin.loaded:
        logger.warn(f'Plugin {name} is not loaded', name='console')
        return
    
    plugin.loaded = False
    if plugin.child_plugins:
        logger.warn(
            f'Plugin {name} is required by '
            f'{"、".join(child.name for child in plugin.child_plugins)} , '
            f'cannnot be unloaded',
            name='console'
        )
        return
    
    logger.info(f'Unloading plugin {name} ...', name='console')
    
    # 清除命令规则
    for processor in plugin.processors:
        for checker in processor.rule.checkers:
            if isinstance(checker.call, CommandRule):
                # 从命令前缀树中移除命令规则
                for command in checker.call.cmds:
                    for start in checker.call.command_start:
                        TrieRule.del_prefix(f'{start}{command}')
    # 卸载插件事件处理器
    for processor in plugin.processors:
        processor.destroy()
    # 终止插件定时任务调度器
    for scheduler in plugin.schedulers:
        scheduler.stop()
    
    # 从 sys.modules 中移除插件模块
    if plugin.module_name in sys.modules:
        del sys.modules[plugin.module_name]
    
    # 从插件集合中移除插件
    _revert_plugin(plugin)
    logger.info(f'Plugin {name} unloaded', name='console')
    return

def _load_plugin(name: str) -> None:
    '''加载插件

    参数:
        name (str): 插件名称
    '''
    plugin = get_plugin(_module_name_to_plugin_name(name))
    if not plugin:
        if manager := _find_manager_by_name(name):
            plugin = manager.load_plugin(name, True)
        else:
            _t = _current_plugin_chain.set(())
            try:
                plugin = load_plugin(name, True)
            finally:
                _current_plugin_chain.reset(_t)
        if not plugin:
            logger.warn(f'Failed to load plugin {name}', name='console')
            return
    else:
        logger.warn(f'Plugin {name} is already loaded', name='console')

def _reload_plugin(name: str) -> None:
    '''重载插件

    参数:
        name (str): 插件名称
    '''
    plugin = get_plugin(name)
    if plugin is None:
        logger.warn(f'Plugin {name} not found', name='console')
        return
    if not plugin.loaded:
        logger.warn(f'Plugin {name} is not loaded', name='console')
        return
    
    logger.info(f'Reloading plugin {name} ...', name='console')
    
    try:
        _unload_plugin(name)
    except Exception:
        logger.error(f'Failed to unload plugin {name}', name='console')
        return
    
    try:
        _load_plugin(name)
    except Exception:
        logger.error(f'Failed to load plugin {name}', name='console')
        return
    
    logger.info(f'Plugin {name} reloaded', name='console')
    return

def _search_plugins(path: str) -> list[str]:
    '''从路径中搜索插件

    参数:
        path (str): 搜索路径
    '''
    result: list[str] = []
    for module_info in iter_modules([path]):
        if module_info.name.startswith('_'):
            continue
        
        if module_info.name in result:
            continue
        
        if not (module_spec := module_info.module_finder.find_spec(module_info.name, None)):
            continue
        
        if not module_spec.origin:
            continue
        result.append(module_info.name)
    return result

@loop
def _console() -> None:
    cmd = ''
    try:
        cmd = input('AnonBot> ')
    except KeyboardInterrupt:
        if _driver is not None:
            _driver._handle_exit(signal.SIGINT, None)
        else:
            sys.exit(0)
    if cmd == '':
        return
    
    if cmd.startswith('plugins'):
        if cmd.lstrip('plugins').strip() == '':
            for plugin in get_loaded_plugins():
                print(plugin.name)
        else:
            if cmd.lstrip('plugins').strip() == 'help':
                print(
                    'plugins: 列出已加载的插件'
                )
            else:
                print(
                    '"plugins" command does not accept any arguments, \n'
                    'use "help" command to get help'
                )
    elif cmd.startswith('search'):
        path_name = cmd.lstrip('search').strip()
        if path_name == '':
            print(
                '"search" command requires a path name, \n'
                'use "help" command to get help'
            )
        elif path_name == 'help':
            print(
                'search <path_name>: 搜索指定路径中的可用插件'
            )
        else:
            result = _search_plugins(path_name)
            if not result:
                print(f'No loadable plugin found in path {path_name}')
            else:
                print('Loadable plugins:')
                for plugin in result:
                    print('-', plugin)
    elif cmd.startswith('load'):
        plugin_name = cmd.lstrip('load').strip()
        if plugin_name == '':
            print(
                '"load" command requires a plugin name with path, \n'
                'use "help" command to get help'
            )
        elif plugin_name == 'help':
            print(
                'load <path_name.plugin_name>: 加载指定路径插件'
            )
        else:
            _load_plugin(plugin_name)
    elif cmd.startswith('unload'):
        plugin_name = cmd.lstrip('unload').strip()
        if plugin_name == '':
            print(
                '"unload" command requires a plugin name, \n'
                'use "help" command to get help'
            )
        elif plugin_name == 'help':
            print(
                'unload <plugin_name>: 卸载指定插件'
            )
        else:
            plugin = get_plugin(plugin_name)
            if plugin is None:
                print(f'Plugin {plugin_name} not found, please check the name')
            else:
                _unload_plugin(plugin.name)
    elif cmd.startswith('reload'):
        plugin_name = cmd.lstrip('reload').strip()
        if plugin_name == '':
            print(
                '"reload" command requires a plugin name, \n'
                'use "help" command to get help'
            )
        elif plugin_name == 'help':
            print(
                'reload <plugin_name>: 重载指定插件'
            )
        else:
            plugin = get_plugin(plugin_name)
            if plugin is None:
                print(f'Plugin {plugin_name} not found, please check the name')
            else:
                _reload_plugin(plugin.name)
    elif cmd.startswith('exit'):
        if cmd.lstrip('exit').strip() == '':
            if _driver is not None:
                _driver._handle_exit(signal.SIGINT, None)
            else:
                sys.exit(0)
        else:
            if cmd.lstrip('exit').strip() == 'help':
                print(
                    'exit: 退出控制台'
                )
            else:
                print(
                    '"exit" command does not accept any arguments, \n'
                    'use "help" command to get help\n'
                )
    elif cmd.startswith('help'):
        print(
            'AnonBot 控制台命令列表\n'
            '    help: 获取帮助\n'
            '    plugins: 列出已加载的插件\n'
            '    search <path_name>: 搜索指定路径中的可用插件\n'
            '    load <path_name.plugin_name>: 加载指定路径插件\n'
            '    unload <plugin_name>: 卸载指定插件\n'
            '    reload <plugin_name>: 重载指定插件\n'
            '    exit: 退出 AnonBot\n'
        )
    else:
        print(
            f'Command {cmd} is not an available command\n'
            'use "help" command to get help'
        )

def run(driver: 'Driver') -> None:
    '''启动控制台'''
    global _driver
    _driver = driver
    create_task(Task(_console))
