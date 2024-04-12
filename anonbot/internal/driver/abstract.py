import abc
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Callable, Type

from anonbot.threading import Task
from anonbot.log import logger
from anonbot.config import Config

from .model import Request, Response, WebSocket, HTTPServerSetup

if TYPE_CHECKING:
    from anonbot.internal.adapter import Bot, Adapter

class Driver(abc.ABC):
    '''驱动器基类。

    一个驱动器负责控制一个适配器的启动与停止。

    参数:
        config (Config): 驱动器配置
    '''
    _adapters: dict[str, 'Adapter'] = {}
    '''驱动器注册的适配器'''
    
    def __init__(self, config: Config) -> None:
        self.config: Config = config
        '''驱动器配置'''
        self._bots: dict[str, 'Bot'] = {}
        self._bot_tasks: set[Task] = set()
    
    def __repr__(self) -> str:
        return (
            f'Driver(type={self.type!r}, '
            f'adapters={len(self._adapters)}, bots={len(self._bots)})'
        )
    
    @property
    def bots(self) -> dict[str, 'Bot']:
        '''获取当前所有已连接的 Bot'''
        return self._bots
    
    def register_adapter(self, adapter: Type['Adapter'], name: str = '', **kwargs) -> None:
        '''注册协议适配器

        参数:
            adapter (Adapter): 协议适配器类
            name (str): 适配器名称 (默认为适配器类的名称)
            **kwargs (Any): 传递给适配器的参数
        '''
        if name == '':
            name = adapter.get_name()
        if name in self._adapters:
            logger.warn(f'Adapter {name} 已被注册')
            return
        self._adapters[name] = adapter(self, **kwargs)
        logger.debug(f'{self} 成功注册 adapter {name}')
    
    @property
    @abc.abstractmethod
    def type(self) -> str:
        '''驱动器类型名称'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def run(self, *args, **kwargs) -> None:
        '''启动驱动器'''
        logger.debug(f'Adapters Loaded: {", ".join(self._adapters)}')
    
    @abc.abstractmethod
    def on_startup(self, func: Callable) -> Callable:
        """注册一个在驱动器启动时执行的函数"""
        raise NotImplementedError

    @abc.abstractmethod
    def on_shutdown(self, func: Callable) -> Callable:
        """注册一个在驱动器停止时执行的函数"""
        raise NotImplementedError
    
    def _bot_connect(self, bot: 'Bot', platform: str) -> None:
        '''连接成功后，调用此函数来注册 bot 对象'''
        if f'{platform}:{bot.self_id}' in self._bots:
            raise RuntimeError(f'Bot {bot.self_id} 发生重复连接')
        self._bots[f'{platform}:{bot.self_id}'] = bot
    
    def _bot_disconnect(self, bot: 'Bot', platform: str) -> None:
        '''连接断开后，调用此函数来注销 bot 对象'''
        if f'{platform}:{bot.self_id}' in self._bots:
            del self._bots[f'{platform}:{bot.self_id}']
    
    def _cleanup(self) -> None:
        '''清理驱动器资源'''
        if self._bot_tasks:
            logger.debug(f'{self} waiting for bot tasks...')
            for task in self._bot_tasks:
                task.cancel()

class Mixin(abc.ABC):
    '''与其他驱动器共用的混入基类。'''
    
    @property
    @abc.abstractmethod
    def type(self) -> str:
        '''混入驱动器类型名称'''
        raise NotImplementedError

class ClientMixin(Mixin):
    '''客户端混入基类。'''

class ServerMixin(Mixin):
    '''服务器混入基类。'''
    
    @abc.abstractmethod
    def startup(self, *args, **kwargs) -> None:
        '''启动服务器'''
        raise NotImplementedError

class HTTPClientMixin(ClientMixin):
    '''HTTP 客户端混入基类。'''
    
    @abc.abstractmethod
    def request(self, setup: Request) -> Response:
        '''发送一个 HTTP 请求'''
        raise NotImplementedError

class WebSocketClientMixin(ClientMixin):
    '''WebSocket 客户端混入基类。'''
    
    @abc.abstractmethod
    @contextmanager
    def websocket(self, setup: Request) -> Generator[WebSocket, None, None]:
        '''发起一个 WebSocket 连接'''
        raise NotImplementedError
        yield

class WSGIMixin(ServerMixin):
    '''WSGI 服务器混入基类。'''
    
    @property
    @abc.abstractmethod
    def server_app(self) -> Any:
        '''驱动 APP 对象'''
        raise NotImplementedError
    
    @property
    @abc.abstractmethod
    def wsgi(self) -> Any:
        '''驱动 WSGI 对象'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def setup_http_server(self, setup: HTTPServerSetup) -> None:
        '''设置一个 HTTP 服务器路由配置'''
        raise NotImplementedError
