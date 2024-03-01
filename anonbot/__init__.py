'''AnonBot 启动入口'''

from importlib.metadata import version
from typing import Any, Type, Union, TypeVar, Optional, overload

from anonbot.config import Config
from anonbot.log import logger as logger
from anonbot.adapter import Bot, Adapter
from anonbot.driver.general import Driver as GeneralDriver
from anonbot.driver import Driver, Mixin, WSGIMixin, combine_driver

try:
    __version__ = version('anonbot')
except Exception:
    __version__ = None

A = TypeVar('A', bound=Adapter)

_driver: Optional[Driver] = None

def get_driver() -> Driver:
    '''获取全局驱动器实例'''
    if _driver is None:
        raise ValueError('Driver not initialized')
    return _driver

@overload
def get_adapter(name: str) -> Adapter:
    '''根据名称获取适配器对象

    参数:
        name (str): 适配器名称

    返回:
        Adapter: 指定名称的适配器对象
    '''
    ...

@overload
def get_adapter(name: Type[A]) -> A:
    '''根据名称获取适配器对象

    参数:
        name (Type[A]): 适配器类

    返回:
        A: 指定类型的适配器对象
    '''
    ...

def get_adapter(name: Union[str, Type[Adapter]]) -> Adapter:
    '''根据名称获取适配器对象'''
    adapters = get_adapters()
    target = name if isinstance(name, str) else name.get_name()
    if target not in adapters:
        raise ValueError(f'Adapter "{target}" not registered')
    return adapters[target]

def get_adapters() -> dict[str, Adapter]:
    '''获取所有已注册的适配器'''
    return get_driver()._adapters.copy()

def get_app() -> Any:
    '''获取全局 `anonbot.driver.WSGIMixin` 实例'''
    driver = get_driver()
    assert isinstance(driver, WSGIMixin), 'Driver is not WSGI compatible'
    return driver.server_app

def get_wsgi() -> Any:
    '''获取全局 WSGI 服务器实例'''
    driver = get_driver()
    assert isinstance(driver, WSGIMixin), 'Driver is not WSGI compatible'
    return driver.wsgi

def get_bot(self_id: Optional[str] = None) -> Bot:
    '''获取一个连接到 AnonBot 的 `anonbot.adapter.Bot` 实例'''
    bots = get_bots()
    if self_id is not None:
        return bots[self_id]
    
    for bot in bots.values():
        return bot
    
    raise ValueError('No bot connected')

def get_bots() -> dict[str, Bot]:
    '''获取所有连接到 AnonBot 的 `anonbot.adapter.Bot` 实例'''
    return get_driver().bots

def _combine_drivers() -> Type[Driver]:
    '''尝试组合全部可用驱动'''
    mixins: list[Type[Mixin]] = []
    try:
        from anonbot.driver.websocket import Mixin as WebSocketMixin
        mixins.append(WebSocketMixin)
    except ImportError:
        pass
    try:
        from anonbot.driver.flask import Mixin as FlaskMixin
        mixins.append(FlaskMixin)
    except ImportError:
        pass
    try:
        from anonbot.driver.httpx import Mixin as HTTPXMixin
        mixins.append(HTTPXMixin)
    except ImportError:
        pass
    if not mixins:
        raise ImportError('No driver available')
    return combine_driver(GeneralDriver, *mixins)

def init(path: str) -> None:
    '''初始化 AnonBot 以及驱动器

    参数:
        path (str): 配置文件路径
    '''
    global _driver
    if not _driver:
        logger.info('Initializing AnonBot')
        config = Config.load_from_yaml(path)
        DriverClass = _combine_drivers()
        _driver = DriverClass(config)
        logger.set_level(config.log_level)

def run(*args: Any, **kwargs: Any) -> None:
    '''启动 AnonBot'''
    get_driver().run(*args, **kwargs)

from anonbot.plugin import on as on
from anonbot.plugin import on_type as on_type
from anonbot.plugin import on_regex as on_regex
from anonbot.plugin import on_command as on_command
from anonbot.plugin import on_keyword as on_keyword
from anonbot.plugin import load_plugin as load_plugin
from anonbot.plugin import on_endswith as on_endswith
from anonbot.plugin import on_internal as on_internal
from anonbot.plugin import load_plugins as load_plugins
from anonbot.plugin import on_fullmatch as on_fullmatch
from anonbot.plugin import on_startswith as on_startswith
from anonbot.plugin import on_guild_added as on_guild_added
from anonbot.plugin import on_login_added as on_login_added
from anonbot.plugin import on_guild_removed as on_guild_removed
from anonbot.plugin import on_guild_request as on_guild_request
from anonbot.plugin import on_login_removed as on_login_removed
from anonbot.plugin import on_login_updated as on_login_updated
from anonbot.plugin import on_friend_request as on_friend_request
from anonbot.plugin import on_reaction_added as on_reaction_added
from anonbot.plugin import on_message_created as on_message_created
from anonbot.plugin import on_message_deleted as on_message_deleted
from anonbot.plugin import on_message_updated as on_message_updated
from anonbot.plugin import on_reaction_removed as on_reaction_removed
from anonbot.plugin import on_guild_member_added as on_guild_member_added
from anonbot.plugin import on_guild_role_created as on_guild_role_created
from anonbot.plugin import on_guild_role_deleted as on_guild_role_deleted
from anonbot.plugin import on_guild_role_updated as on_guild_role_updated
from anonbot.plugin import on_interaction_button as on_interaction_button
from anonbot.plugin import on_interaction_command as on_interaction_command
from anonbot.plugin import on_guild_member_removed as on_guild_member_removed
from anonbot.plugin import on_guild_member_request as on_guild_member_request
from anonbot.plugin import on_guild_member_updated as on_guild_member_updated
