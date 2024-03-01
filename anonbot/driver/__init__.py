'''AnonBot 驱动适配器基类'''
from anonbot.internal.driver import URL as URL
from anonbot.internal.driver import Mixin as Mixin
from anonbot.internal.driver import Driver as Driver
from anonbot.internal.driver import Cookies as Cookies
from anonbot.internal.driver import Request as Request
from anonbot.internal.driver import Response as Response
from anonbot.internal.driver import WSGIMixin as WSGIMixin
from anonbot.internal.driver import WebSocket as WebSocket
from anonbot.internal.driver import ClientMixin as ClientMixin
from anonbot.internal.driver import HTTPVersion as HTTPVersion
from anonbot.internal.driver import ServerMixin as ServerMixin
from anonbot.internal.driver import combine_driver as combine_driver
from anonbot.internal.driver import HTTPClientMixin as HTTPClientMixin
from anonbot.internal.driver import HTTPServerSetup as HTTPServerSetup
from anonbot.internal.driver import WebSocketClientMixin as WebSocketClientMixin
from anonbot.internal.driver import WebSocketServerSetup as WebSocketServerSetup

__autodoc__ = {
    'URL': True,
    'Mixin': True,
    'Driver': True,
    'Cookies': True,
    'Request': True,
    'Response': True,
    'WSGIMixin': True,
    'WebSocket': True,
    'ClientMixin': True,
    'HTTPVersion': True,
    'ServerMixin': True,
    'combine_driver': True,
    'HTTPClientMixin': True,
    'HTTPServerSetup': True,
    'WebSocketClientMixin': True,
    'WebSocketServerSetup': True
}