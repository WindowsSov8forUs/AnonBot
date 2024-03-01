'''websocket 驱动适配'''

import logging
from functools import wraps
from contextlib import contextmanager
from typing_extensions import override
from typing import Union, TypeVar, Callable, Generator, ParamSpec

from anonbot.driver import Request
from anonbot.log import LoggingHandler
from anonbot.exception import WebSocketClosed
from anonbot.driver import WebSocketClientMixin
from anonbot.driver import WebSocket as BaseWebSocket

from websocket import WebSocket as WebSocketClient
from websocket import ABNF, WebSocketConnectionClosedException, create_connection

T = TypeVar('T')
P = ParamSpec('P')

logger = logging.Logger('websocket.client', 'INFO')
logger.addHandler(LoggingHandler())

def catch_closed(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def decorator(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except WebSocketConnectionClosedException as exception:
            raise WebSocketClosed(1000, 'WebSocket 已关闭')
        except Exception as exception:
            raise exception
    
    return decorator

class Mixin(WebSocketClientMixin):
    '''websocket 混入驱动适配'''
    
    @property
    @override
    def type(self) -> str:
        return 'websocket'
    
    @override
    @contextmanager
    def websocket(self, setup: Request) -> Generator["WebSocket", None, None]:
        ws = create_connection(
            str(setup.url),
            timeout=setup.timeout,
            header={**setup.headers, **setup.cookies.as_header(setup)}
        )
        
        try:
            yield WebSocket(request=setup, websocket=ws)
        finally:
            ws.close()

class WebSocket(BaseWebSocket):
    '''Websocket WebSocket 适配'''
    
    @override
    def __init__(self, *, request: Request, websocket: WebSocketClient) -> None:
        super().__init__(request=request)
        self.websocket = websocket
    
    @property
    @override
    def closed(self) -> bool:
        return not self.websocket.connected
    
    @override
    def accept(self) -> None:
        raise NotImplementedError
    
    @override
    def close(self, code: int = 1000, reason: str = '') -> None:
        self.websocket.close(status=code, reason=reason.encode('utf-8'))
    
    @override
    @catch_closed
    def receive(self) -> Union[str, bytes]:
        opcode, data = self.websocket.recv_data()
        if opcode == ABNF.OPCODE_CLOSE and isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                reason = data.decode('utf-8')
            else:
                assert isinstance(data, str), "data must be a str or bytes"
                reason = data
            raise WebSocketClosed(1000, reason)
        
        return data
    
    @override
    @catch_closed
    def receive_text(self) -> str:
        opcode, data = self.websocket.recv_data()
        if opcode == ABNF.OPCODE_CLOSE and isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                reason = data.decode('utf-8')
            else:
                assert isinstance(data, str), "data must be a str or bytes"
                reason = data
            raise WebSocketClosed(1000, reason)
        
        if not isinstance(data, str):
            raise TypeError('WebSocket 接收到的为非文本数据')
        
        return data
    
    @override
    @catch_closed
    def receive_bytes(self) -> bytes:
        opcode, data = self.websocket.recv_data()
        if opcode == ABNF.OPCODE_CLOSE and isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                reason = data.decode('utf-8')
            else:
                assert isinstance(data, str), "data must be a str or bytes"
                reason = data
            raise WebSocketClosed(1000, reason)
        
        if not isinstance(data, bytes):
            raise TypeError('WebSocket 接收到的为非字节数据')
        
        return data
    
    @override
    def send_text(self, data: str) -> None:
        self.websocket.send(data)
    
    @override
    def send_bytes(self, data: bytes) -> None:
        self.websocket.send(data)
