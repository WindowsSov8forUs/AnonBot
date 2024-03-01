import abc
from contextlib import contextmanager
from typing import Any, Generator

from anonbot.config import Config, BaseConfig
from anonbot.internal.driver import (
    Driver,
    Request,
    Response,
    WSGIMixin,
    WebSocket,
    HTTPClientMixin,
    HTTPServerSetup,
    WebSocketClientMixin
)

from .bot import Bot

class Adapter(abc.ABC):
    '''协议适配器基类'''
    
    def __init__(self, driver: Driver, **kwargs: Any) -> None:
        self.driver: Driver = driver
        '''协议适配器所属的 `anonbot.internal.driver.Driver` 实例'''
        self.bots: dict[str, Bot] = {}
        '''本协议适配器已建立连接的 `anonbot.adapters.Bot` 实例'''
        try:
            self._config: dict[str, Any] = self.config.get(self.get_name().lower(), {})
        except AttributeError:
            self._config = {}
    
    def __repr__(self) -> str:
        return f'Adapter(name={self.get_name()!r})'
    
    @classmethod
    @abc.abstractmethod
    def get_name(cls) -> str:
        '''当前协议适配器名称'''
        raise NotImplementedError
    
    @property
    def config(self) -> Config:
        '''当前 AnonBot 配置'''
        return self.driver.config
    
    def bot_connect(self, bot: Bot, platform: str) -> None:
        '''告知 AnonBot 建立了一个新的 `anonbot.adapters.Bot` 连接
    
        参数:
            bot (Bot): `anonbot.adapters.Bot` 实例
            platform (str): 平台名称
        '''
        self.driver._bot_connect(bot, platform)
        self.bots[f'{platform}:{bot.self_id}'] = bot
    
    def bot_disconnect(self, bot: Bot) -> None:
        '''告知 AnonBot 断开了一个 `anonbot.adapters.Bot` 连接
    
        参数:
            bot (Bot): `anonbot.adapters.Bot` 实例
        '''
        if self.bots.pop(bot.self_id, None) is None:
            raise RuntimeError(f'{bot} not found in adapter {self.get_name()}')
        self.driver._bot_disconnect(bot)
    
    def setup_http_server(self, setup: HTTPServerSetup) -> None:
        '''设置一个 HTTP 服务器路由配置'''
        if not isinstance(self.driver, WSGIMixin):
            raise TypeError('Current driver does not support http server')
        self.driver.setup_http_server(setup)
    
    def request(self, setup: Request) -> Response:
        '''进行一个 HTTP 客户端请求'''
        if not isinstance(self.driver, HTTPClientMixin):
            raise TypeError('Current driver does not support http client')
        return self.driver.request(setup)
    
    @contextmanager
    def websocket(self, setup: Request) -> Generator[WebSocket, None, None]:
        '''建立一个 WebSocket 客户端连接请求'''
        if not isinstance(self.driver, WebSocketClientMixin):
            raise TypeError('Current driver does not support websocket client')
        with self.driver.websocket(setup) as websocket:
            yield websocket
    
    @abc.abstractmethod
    def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        '''`Adapter` 实际调用 api 的逻辑实现函数。

        参数:
            api (str): API 名称
            **data (Any): API 数据
        '''
        raise NotImplementedError

__autodoc__ = {'Adapter._call_api': True}
