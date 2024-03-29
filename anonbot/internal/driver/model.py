import abc
import urllib.request
from enum import Enum
from dataclasses import dataclass
from http.cookiejar import Cookie, CookieJar
from typing import (
    IO,
    Any,
    Union,
    Mapping,
    Callable,
    Iterator,
    Optional,
    TypeAlias,
    MutableMapping
)

from yarl import URL
from multidict import  CIMultiDict

RawURL: TypeAlias = tuple[bytes, bytes, Optional[int], bytes]

SimpleQuery: TypeAlias = Union[str, int, float]
QueryVariable: TypeAlias = Union[SimpleQuery, list[SimpleQuery]]
QueryTypes: TypeAlias = Union[
    None, str, Mapping[str, QueryVariable], list[tuple[str, QueryVariable]]
]

HeaderTypes: TypeAlias = Union[None, CIMultiDict[str], dict[str, str], list[tuple[str, str]]]

CookieTypes: TypeAlias = Union[None, 'Cookies', CookieJar, dict[str, str], list[tuple[str, str]]]

ContentTypes: TypeAlias = Union[str, bytes, None]
DataTypes: TypeAlias = Union[dict, None]
FileContent: TypeAlias = Union[IO[bytes], bytes]
FileType: TypeAlias = tuple[Optional[str], FileContent, Optional[str]]
FileTypes: TypeAlias = Union[FileContent, tuple[Optional[str], FileContent], FileType]
FilesTypes: TypeAlias = Union[dict[str, FileTypes], list[tuple[str, FileTypes]], None]

class HTTPVersion(Enum):
    H10 = '1.0'
    H11 = '1.1'
    H2 = '2'

class Request:
    def __init__(
        self,
        method: Union[str, bytes],
        url: Union['URL', str, RawURL],
        *,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        content: ContentTypes = None,
        data: DataTypes = None,
        json: Any = None,
        files: FilesTypes = None,
        version: Union[str, HTTPVersion] = HTTPVersion.H11,
        timeout: Optional[float] = None,
        proxy: Optional[str] = None
    ):
        if isinstance(method, bytes):
            self.method = method.decode('ascii').upper()
        else:
            assert isinstance(method, str), "method must be a str or bytes"
            self.method = method.upper()
        
        self.version: HTTPVersion = HTTPVersion(version)
        self.timeout: Optional[float] = timeout
        self.proxy: Optional[str] = proxy
        
        # url
        if isinstance(url, tuple):
            scheme, host, port, path = url
            url = URL.build(
                scheme=scheme.decode('ascii'),
                host=host.decode('ascii'),
                port=port,
                path=path.decode('ascii'),
            )
        else:
            url = URL(url)
        
        if params is not None:
            url = url.update_query(params)
        self.url: URL = url
        
        self.headers: CIMultiDict[str] = (
            CIMultiDict(headers) if headers is not None else CIMultiDict()
        )
        self.cookies = Cookies(cookies)
        
        # body
        self.content: ContentTypes = content
        self.data: DataTypes = data
        self.json: Any = json
        self.files: Optional[list[tuple[str, FileType]]] = None
        if files:
            self.files = []
            files_ = files.items() if isinstance(files, dict) else files
            for name, file_info in files_:
                if not isinstance(file_info, tuple):
                    self.files.append((name, (name, file_info, None)))
                elif len(file_info) == 2:
                    self.files.append((name, (file_info[0], file_info[1], None)))
                else:
                    self.files.append((name, file_info))
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(method={self.method!r}, url={self.url!s})'

class Response:
    def __init__(
        self,
        status_code: int,
        *,
        headers: HeaderTypes = None,
        content: ContentTypes = None,
        request: Optional[Request] = None
    ):
        self.status_code: int = status_code
        self.headers: CIMultiDict[str] = (
            CIMultiDict(headers) if headers is not None else CIMultiDict()
        )
        self.content: ContentTypes = content
        self.request: Optional[Request] = request
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(status_code={self.status_code!r})'

class WebSocket(abc.ABC):
    def __init__(self, *, request: Request):
        self.request: Request = request
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.request.url!s}")'
    
    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        '''连接是否已关闭'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def accept(self) -> None:
        '''接受 WebSocket 连接请求'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def close(self, code: int = 1000, reason: str = '') -> None:
        '''关闭 WebSocket 连接请求'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def receive(self) -> Union[str, bytes]:
        '''接收一条 WebSocket text/bytes 信息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def receive_text(self) -> str:
        '''接收一条 WebSocket text 信息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def receive_bytes(self) -> bytes:
        '''接收一条 WebSocket bytes 信息'''
        raise NotImplementedError
    
    def send(self, data: Union[str, bytes]) -> None:
        '''发送一条 WebSocket text/bytes 信息'''
        if isinstance(data, str):
            self.send_text(data)
        elif isinstance(data, bytes):
            self.send_bytes(data)
        else:
            raise TypeError('WebSocket send message must be str or bytes')
    
    @abc.abstractmethod
    def send_text(self, data: str) -> None:
        '''发送一条 WebSocket text 信息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def send_bytes(self, data: bytes) -> None:
        '''发送一条 WebSocket bytes 信息'''
        raise NotImplementedError

class Cookies(MutableMapping):
    def __init__(self, cookies: CookieTypes = None):
        self.jar: CookieJar = cookies if isinstance(cookies, CookieJar) else CookieJar()
        if cookies is not None and not isinstance(cookies, CookieJar):
            if isinstance(cookies, dict):
                for key, value in cookies.items():
                    self.set(key, value)
            elif isinstance(cookies, list):
                for key, value in cookies:
                    self.set(key, value)
            elif isinstance(cookies, Cookies):
                for cookie in cookies.jar:
                    self.jar.set_cookie(cookie)
            else:
                raise TypeError(f'Cookies must be dict or list, got {type(cookies)}')
    
    def set(self, name: str, value: str, domain: str = '', path: str = '/') -> None:
        cookie = Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=bool(domain),
            domain_initial_dot=domain.startswith('.'),
            path=path,
            path_specified=bool(path),
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
            rfc2109=False
        )
        self.jar.set_cookie(cookie)
    
    def get(
        self,
        name: str,
        default: Optional[str] = None,
        domain: Optional[str] = None,
        path: Optional[str] = None
    ) -> Optional[str]:
        value: Optional[str] = None
        for cookie in self.jar:
            if (
                cookie.name == name
                and (domain is None or cookie.domain == domain)
                and (path is None or cookie.path == path)
            ):
                if value is not None:
                    message = f'Multiple cookies with name {name!r} found'
                    raise ValueError(message)
                value = cookie.value
        
        return value if value is not None else default
    
    def delete(
        self,
        name: str,
        domain: Optional[str] = None,
        path: Optional[str] = None
    ) -> None:
        if domain is not None and path is not None:
            return self.jar.clear(domain, path, name)
        
        remove = [
            cookie for cookie in self.jar if (
                cookie.name == name
                and (domain is None or cookie.domain == domain)
                and (path is None or cookie.path == path)
            )
        ]
        
        for cookie in remove:
            self.jar.clear(cookie.domain, cookie.path, cookie.name)
    
    def clear(self, domain: Optional[str] = None, path: Optional[str] = None) -> None:
        self.jar.clear(domain, path)
    
    def update(self, cookies: CookieTypes = None) -> None:
        cookies = Cookies(cookies)
        for cookie in cookies.jar:
            self.jar.set_cookie(cookie)
    
    def as_header(self, request: Request) -> dict[str, str]:
        urllib_request = self._CookieCompatRequest(request)
        self.jar.add_cookie_header(urllib_request)
        return urllib_request.added_headers
    
    def __setitem__(self, name: str, value: str) -> None:
        return self.set(name, value)
    
    def __getitem__(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return value
    
    def __delitem__(self, name: str) -> None:
        return self.delete(name)
    
    def __len__(self) -> int:
        return len(self.jar)
    
    def __iter__(self) -> Iterator[Cookie]:
        return iter(self.jar)
    
    def __repr__(self) -> str:
        cookies_repr = ", ".join(
            f'Cookie({cookie.name}={cookie.value} for {cookie.domain})'
            for cookie in self.jar
        )
        return f'{self.__class__.__name__}({cookies_repr})'
    
    class _CookieCompatRequest(urllib.request.Request):
        def __init__(self, request: Request) -> None:
            super().__init__(
                url=str(request.url),
                headers=dict(request.headers),
                method=request.method,
            )
            self.request = request
            self.added_headers: dict[str, str] = {}

        def add_unredirected_header(self, key: str, value: str) -> None:
            super().add_unredirected_header(key, value)
            self.added_headers[key] = value

@dataclass
class HTTPServerSetup:
    '''HTTP 服务器配置'''
    path: URL
    method: str
    name: str
    handle_func: Callable[[Request], Response]

@dataclass
class WebSocketServerSetup:
    '''WebSocket 服务器配置'''
    path: URL
    name: str
    handle_func: Callable[[WebSocket], Any]