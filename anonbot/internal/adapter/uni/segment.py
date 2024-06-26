'''用于跨平台互通的 UniMessageSegment
所有适配器都需要基于此进行实现
'''
from io import BytesIO
from pathlib import Path
from dataclasses import field, dataclass
from typing_extensions import override
from typing import TYPE_CHECKING, Any, NotRequired, Self, Type, Union, Optional, TypedDict

from anonbot.internal.adapter.message import MessageSegment as BaseMessageSegment

if TYPE_CHECKING:
    from .message import Message

class SrcBase64(TypedDict):
    '''base64 资源元素'''
    data: Union[bytes, BytesIO]
    '''base64 数据'''
    type: str
    '''MIME 类型'''

class MessageSegment(BaseMessageSegment['Message']):
    children: Optional['Message'] = None
    '''子消息链'''
    
    def __str__(self) -> str:
        attrs = ', '.join(f'{k}={v}' for k, v in self.data.items())
        if self.type == 'text' and 'text' in self.data:
            return self.data['text']
        _type = self.type.capitalize() if self.type != 'message' else 'RenderMessage'
        return (
            f'{_type}('
            + attrs
            + (', ' if attrs != '' and self.children is not None else '')
            + (f'children=[{str(self.children)}]' if self.children is not None else '')
            + ')'
        )
    
    def __getattr__(self, name: str) -> Any:
        if name in self.data:
            return self.data[name]
        return None
    
    def __deepcopy__(self, memo: Any) -> 'MessageSegment':
        if type(self) is Other:
            return Other(self.type, **self.data.copy())
        return type(self)(**self.data.copy())
    
    @classmethod
    @override
    def get_message_class(cls) -> Type['Message']:
        return Message
    
    def set_children(self, children: Optional['Message'] = None) -> Self:
        self.children = children
        return self
    
    def set_attr(self, key: str, value: Any) -> Self:
        self.data[key] = value
        return self
    
    @override
    def is_text(self) -> bool:
        return False

class TextData(TypedDict):
    text: str

@dataclass
class Text(MessageSegment):
    data: TextData = field(default_factory=dict) # type: ignore
    
    def __init__(self, text: str) -> None:
        self.type = 'text'
        self.data = {'text': text}
    
    @override
    def __str__(self) -> str:
        return self.data['text']
    
    @override
    def is_text(self) -> bool:
        return True

class AtData(TypedDict):
    id: NotRequired[str]
    name: NotRequired[str]
    role: NotRequired[str]
    type: NotRequired[str]

@dataclass
class At(MessageSegment):
    data: AtData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        type: Optional[str] = None
    ) -> None:
        self.type = 'at'
        self.data: AtData = {}
        if id is not None:
            self.data['id'] = id
        if name is not None:
            self.data['name'] = name
        if role is not None:
            self.data['role'] = role
        if type is not None:
            self.data['type'] = type

class SharpData(TypedDict):
    id: str
    name: NotRequired[str]

@dataclass
class Sharp(MessageSegment):
    data: SharpData = field(default_factory=dict) # type: ignore
    
    def __init__(self, id: str, name: Optional[str] = None) -> None:
        self.type = 'sharp'
        self.data: SharpData = {'id': id}
        if name is not None:
            self.data['name'] = name

class LinkData(TypedDict):
    href: str

@dataclass
class Link(MessageSegment):
    data: LinkData = field(default_factory=dict) # type: ignore
    
    def __init__(self, href: str) -> None:
        self.type = 'link'
        self.data: LinkData = {'href': href}

    @override
    def is_text(self) -> bool:
        return True

class SrcData(TypedDict):
    src: Union[str, Path, BytesIO]
    title: NotRequired[str]
    cache: NotRequired[bool]
    timeout: NotRequired[str]

class ImageData(SrcData, total=False):
    width: NotRequired[int]
    height: NotRequired[int]

@dataclass
class Image(MessageSegment):
    data: ImageData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        src: Union[str, Path, BytesIO],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> None:
        self.type = 'image'
        self.data: ImageData = {'src': src}
        if title is not None:
            self.data['title'] = title
        if cache is not None:
            self.data['cache'] = cache
        if timeout is not None:
            self.data['timeout'] = timeout
        if width is not None:
            self.data['width'] = width
        if height is not None:
            self.data['height'] = height

class AudioData(SrcData, total=False):
    duration: NotRequired[float]
    poster: NotRequired[str]

@dataclass
class Audio(MessageSegment):
    data: AudioData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        src: Union[str, Path, BytesIO],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        duration: Optional[float] = None,
        poster: Optional[str] = None
    ) -> None:
        self.type = 'audio'
        self.data: AudioData = {'src': src}
        if title is not None:
            self.data['title'] = title
        if cache is not None:
            self.data['cache'] = cache
        if timeout is not None:
            self.data['timeout'] = timeout
        if duration is not None:
            self.data['duration'] = duration
        if poster is not None:
            self.data['poster'] = poster

class VideoData(SrcData, total=False):
    width: NotRequired[int]
    height: NotRequired[int]
    duration: NotRequired[float]
    poster: NotRequired[str]

@dataclass
class Video(MessageSegment):
    data: VideoData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        src: Union[str, Path, BytesIO],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[float] = None,
        poster: Optional[str] = None
    ) -> None:
        self.type = 'video'
        self.data: VideoData = {'src': src}
        if title is not None:
            self.data['title'] = title
        if cache is not None:
            self.data['cache'] = cache
        if timeout is not None:
            self.data['timeout'] = timeout
        if width is not None:
            self.data['width'] = width
        if height is not None:
            self.data['height'] = height
        if duration is not None:
            self.data['duration'] = duration
        if poster is not None:
            self.data['poster'] = poster

class FileData(SrcData, total=False):
    poster: NotRequired[str]

@dataclass
class File(MessageSegment):
    data: FileData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        src: Union[str, Path, BytesIO],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        poster: Optional[str] = None
    ) -> None:
        self.type = 'file'
        self.data: FileData = {'src': src}
        if title is not None:
            self.data['title'] = title
        if cache is not None:
            self.data['cache'] = cache
        if timeout is not None:
            self.data['timeout'] = timeout
        if poster is not None:
            self.data['poster'] = poster

class StyleData(TypedDict):
    text: str
    style: str

@dataclass
class Style(MessageSegment):
    data: StyleData = field(default_factory=dict) # type: ignore
    
    def __init__(self, text: str, style: str) -> None:
        self.type = 'style'
        self.data: StyleData = {'text': text, 'style': style}

    @override
    def is_text(self) -> bool:
        return True

class Br(MessageSegment):
    def __init__(self) -> None:
        self.type = 'br'

    @override
    def is_text(self) -> bool:
        return True

class RenderMessageData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]

@dataclass
class RenderMessage(MessageSegment):
    data: RenderMessageData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        id: Optional[str] = None,
        forward: Optional[bool] = None,
        content: Optional[Union[str, MessageSegment, 'Message']] = None
    ) -> None:
        self.type = 'message'
        self.data: RenderMessageData = {}
        if id is not None:
            self.data['id'] = id
        if forward is not None:
            self.data['forward'] = forward
        if content is not None:
            self.set_children(self.get_message_class()(content))

class QuoteData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]

@dataclass
class Quote(MessageSegment):
    data: QuoteData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        id: Optional[str] = None,
        forward: Optional[bool] = None,
        content: Optional[Union[str, MessageSegment, 'Message']] = None
    ) -> None:
        self.type = 'message'
        self.data: QuoteData = {}
        if id is not None:
            self.data['id'] = id
        if forward is not None:
            self.data['forward'] = forward
        if content is not None:
            self.set_children(self.get_message_class()(content))

class AuthorData(TypedDict):
    id: NotRequired[str]
    name: NotRequired[str]
    avatar: NotRequired[str]

@dataclass
class Author(MessageSegment):
    data: AuthorData = field(default_factory=dict) # type: ignore
    
    def __init__(self, id: Optional[str] = None, name: Optional[str] = None, avatar: Optional[str] = None) -> None:
        self.type = 'author'
        self.data: AuthorData = {}
        if id is not None:
            self.data['id'] = id
        if name is not None:
            self.data['name'] = name
        if avatar is not None:
            self.data['avatar'] = avatar

class ButtonData(TypedDict):
    id: NotRequired[str]
    type: NotRequired[str]
    href: NotRequired[str]
    text: NotRequired[str]
    theme: NotRequired[str]

@dataclass
class Button(MessageSegment):
    data: ButtonData = field(default_factory=dict) # type: ignore
    
    def __init__(
        self,
        id: Optional[str] = None,
        type: Optional[str] = None,
        href: Optional[str] = None,
        text: Optional[str] = None,
        theme: Optional[str] = None
    ) -> None:
        self.type = 'button'
        self.data: ButtonData = {}
        if id is not None:
            self.data['id'] = id
        if type is not None:
            self.data['type'] = type
        if href is not None:
            self.data['href'] = href
        if text is not None:
            self.data['text'] = text
        if theme is not None:
            self.data['theme'] = theme

@dataclass
class Other(MessageSegment):
    def __init__(self, type: str, **kwargs: Any) -> None:
        self.type = type
        self.data = kwargs
