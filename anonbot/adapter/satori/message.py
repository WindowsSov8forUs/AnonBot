import re
from pathlib import Path
from base64 import b64encode
from dataclasses import InitVar, field, dataclass
from typing_extensions import override
from typing import Any, NotRequired, Type, Union, Literal, Iterable, Optional, TypedDict, overload

from anonbot.adapter import Message as BaseMessage
from anonbot.internal.adapter.message import SrcBase64
from anonbot.adapter import MessageSegment as BaseMessageSegment

from .element import Element, parse, escape, param_case

class MessageSegment(BaseMessageSegment['Message']):
    def __str__(self) -> str:
        def _attr(key: str, value: Any) -> str:
            if value is None:
                return ''
            key = param_case(key)
            if value is True:
                return f' {key}'
            if value is False:
                return f' no-{key}'
            return f' {key}="{escape(value, True)}"'
        
        attrs = ''.join(_attr(k, v) for k, v in self.data.items())
        if self.type == 'text' and 'text' in self.data:
            return escape(self.data['text'])
        return f'<{self.type}{attrs}/>'
    
    @classmethod
    @override
    def get_message_class(cls) -> Type['Message']:
        return Message
    
    @staticmethod
    @override
    def text(text: str) -> 'Text':
        return Text('text', {'text': text})
    
    @staticmethod
    @overload
    def at(id: str, name: Optional[str] = None) -> 'At': ...
    
    @staticmethod
    @overload
    def at(*, name: Optional[str] = None, role: str) -> 'At': ...
    
    @staticmethod
    @overload
    def at(*,  type: Literal['all', 'here']) -> 'At': ...
    
    @staticmethod
    @override
    def at(
        id: Optional[str]=None,
        name: Optional[str]=None,
        role: Optional[str]=None,
        type: Optional[str]=None
    ) -> 'At':
        data: AtData = {}
        if id is not None:
            data['id'] = id
        if name is not None:
            data['name'] = name
        if role is not None:
            data['role'] = role
        if type is not None:
            data['type'] = type
        return At('at', data)
    
    @staticmethod
    @override
    def sharp(id: str, name: Optional[str]=None) -> 'Sharp':
        data: SharpData = {'id': id}
        if name is not None:
            data['name'] = name
        return Sharp('sharp', data)
    
    @staticmethod
    @override
    def a(href: str) -> 'A':
        return A('a', {'text': href})
    
    @staticmethod
    @override
    def img(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None
    ) -> 'Img':
        if isinstance(src, str):
            # 判断链接或路径
            if re.match(r'^https?://', src):
                data: ImgData = {'src': src}
            else:
                data: ImgData = {'src': Path(src).absolute().as_uri()}
        elif isinstance(src, Path):
            data: ImgData = {'src': src.absolute().as_uri()}
        else:
            bytes_data = src['data'] if isinstance(src['data'], bytes) else src['data'].getvalue() # type: ignore
            data: ImgData = {'src': f'data:{src["mime"]};base64,{b64encode(bytes_data).decode()}'}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        return Img('img', data)
    
    @staticmethod
    @override
    def audio(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        poster: Optional[str] = None
    ) -> 'Audio':
        if isinstance(src, str):
            # 判断链接或路径
            if re.match(r'^https?://', src):
                data: AudioData = {'src': src}
            else:
                data: AudioData = {'src': Path(src).absolute().as_uri()}
        elif isinstance(src, Path):
            data: AudioData = {'src': src.absolute().as_uri()}
        else:
            bytes_data = src['data'] if isinstance(src['data'], bytes) else src['data'].getvalue() # type: ignore
            data: AudioData = {'src': f'data:{src["mime"]};base64,{b64encode(bytes_data).decode()}'}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        if poster is not None:
            data['poster'] = poster
        return Audio('audio', data)
    
    @staticmethod
    @override
    def video(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        poster: Optional[str] = None
    ) -> 'Video':
        if isinstance(src, str):
            # 判断链接或路径
            if re.match(r'^https?://', src):
                data: VideoData = {'src': src}
            else:
                data: VideoData = {'src': Path(src).absolute().as_uri()}
        elif isinstance(src, Path):
            data: VideoData = {'src': src.absolute().as_uri()}
        else:
            bytes_data = src['data'] if isinstance(src['data'], bytes) else src['data'].getvalue() # type: ignore
            data: VideoData = {'src': f'data:{src["mime"]};base64,{b64encode(bytes_data).decode()}'}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        if poster is not None:
            data['poster'] = poster
        return Video('video', data)
    
    @staticmethod
    @override
    def file(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        poster: Optional[str] = None
    ) -> 'File':
        if isinstance(src, str):
            # 判断链接或路径
            if re.match(r'^https?://', src):
                data: FileData = {'src': src}
            else:
                data: FileData = {'src': Path(src).absolute().as_uri()}
        elif isinstance(src, Path):
            data: FileData = {'src': src.absolute().as_uri()}
        else:
            bytes_data = src['data'] if isinstance(src['data'], bytes) else src['data'].getvalue() # type: ignore
            data: FileData = {'src': f'data:{src["mime"]};base64,{b64encode(bytes_data).decode()}'}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        if poster is not None:
            data['poster'] = poster
        return File('file', data)
    
    @staticmethod
    @override
    def b(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['b']})
    
    @staticmethod
    @override
    def i(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['i']})
    
    @staticmethod
    @override
    def u(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['u']})
    
    @staticmethod
    @override
    def s(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['s']})
    
    @staticmethod
    @override
    def spl(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['spl']})
    
    @staticmethod
    @override
    def code(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['code']})
    
    @staticmethod
    @override
    def sup(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['sup']})
    
    @staticmethod
    @override
    def sub(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['sub']})
    
    @staticmethod
    @override
    def br() -> 'Br':
        return Br('br', {'text': '\n'})
    
    @staticmethod
    @override
    def p(child: Union[str, 'MessageSegment', Iterable['MessageSegment']]) -> 'Style':
        return Style('style', {'children': MessageSegment.text(child) if isinstance(child, str) else child, 'styles': ['p']})
    
    @staticmethod
    @override
    def message(
        id: Optional[str]=None,
        forward: Optional[bool]=None,
        message: Optional[Union[str, 'MessageSegment', Iterable['MessageSegment']]]=None
    ) -> 'RenderMessage':
        data = {}
        if id:
            data['id'] = id
        if forward is not None:
            data['forward'] = forward
        if message:
            data['content'] = Message(message)
        return RenderMessage('message', data) # type: ignore
    
    @staticmethod
    @override
    def quote(
        id: Optional[str]=None,
        forward: Optional[bool]=None,
        message: Optional[Union[str, 'MessageSegment', Iterable['MessageSegment']]]=None
    ) -> 'Quote':
        data = {'content': Message()}
        if id is not None or forward is not None:
            data['content'] += MessageSegment.message(id, forward)
        if message:
            data['content'] += message
        return Quote('quote', data) # type: ignore
    
    @staticmethod
    @override
    def author(
        id: Optional[str]=None,
        name: Optional[str]=None,
        avatar: Optional[str]=None
    ) -> 'Author':
        data = {}
        if id is not None:
            data['id'] = id
        if name is not None:
            data['name'] = name
        if avatar is not None:
            data['avatar'] = avatar
        return Author('author', data) # type: ignore
    
    @staticmethod
    @override
    def button(
        id: Optional[str]=None,
        type: Optional[Literal['action', 'link', 'input']]=None,
        href: Optional[str]=None,
        text: Optional[str]=None,
        theme: Optional[str]=None
    ) -> 'Button':
        data = {}
        if id is not None:
            data['id'] = id
        if type is not None:
            data['type'] = type
        if href is not None:
            data['href'] = href
        if text is not None:
            data['text'] = text
        if theme is not None:
            data['theme'] = theme
        return Button('button', data) # type: ignore
    
    @staticmethod
    def passive(
        id: Optional[str]=None,
        seq: Optional[int]=None
    ) -> 'Passive':
        '''创建一个被动消息段

        参数:
            id (str, optional): 消息 ID
            seq (int, optional): 消息序号

        返回:
            Passive: 被动消息段
        '''
        data: PassiveData = {}
        if id is not None:
            data['id'] = id
        if seq is not None:
            data['seq'] = seq
        return Passive('passive', data)
    
    @override
    def is_text(self) -> bool:
        return False

class TextData(TypedDict):
    text: str

@dataclass
class Text(MessageSegment):
    data: TextData = field(default_factory=dict) # type: ignore
    
    @override
    def __str__(self) -> str:
        return escape(self.data['text'])
    
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

class SharpData(TypedDict):
    id: str
    name: NotRequired[str]

@dataclass
class Sharp(MessageSegment):
    data: SharpData = field(default_factory=dict) # type: ignore

class AData(TypedDict):
    text: str

class A(MessageSegment):
    data: AData = field(default_factory=dict) # type: ignore
    
    @override
    def __str__(self) -> str:
        if 'display' in self.data:
            return f'<a href="{escape(self.data["text"])}" display="{escape(self.data["display"])}"/>'
        return f'<a href="{escape(self.data["text"])}/>'
    
    @override
    def is_text(self) -> bool:
        return True

class ImgData(TypedDict):
    src: str
    title: NotRequired[str]
    cache: NotRequired[bool]
    timeout: NotRequired[str]
    width: NotRequired[int]
    height: NotRequired[int]

@dataclass
class Img(MessageSegment):
    data: ImgData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class AudioData(TypedDict):
    src: str
    title: NotRequired[str]
    cache: NotRequired[bool]
    timeout: NotRequired[str]
    duration: NotRequired[int]
    poster: NotRequired[str]

@dataclass
class Audio(MessageSegment):
    data: AudioData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class VideoData(TypedDict):
    src: str
    title: NotRequired[str]
    cache: NotRequired[bool]
    timeout: NotRequired[str]
    duration: NotRequired[int]
    poster: NotRequired[str]
    width: NotRequired[int]
    height: NotRequired[int]

@dataclass
class Video(MessageSegment):
    data: VideoData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class FileData(TypedDict):
    src: str
    title: NotRequired[str]
    cache: NotRequired[bool]
    timeout: NotRequired[str]
    poster: NotRequired[str]

@dataclass
class File(MessageSegment):
    data: FileData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class StyleData(TypedDict):
    children: 'Message'
    styles: list[str]

class Style(MessageSegment):
    data: StyleData = field(default_factory=dict) # type: ignore
    
    @override
    def __str__(self) -> str:
        prefix = ''.join(f'<{style}>' for style in self.data['styles'])
        suffix = ''.join(f'</{style}>' for style in reversed(self.data['styles']))
        return f'{prefix}{self.data["children"]}{suffix}'
    
    @override
    def is_text(self) -> bool:
        return True

class Br(MessageSegment):
    @override
    def __str__(self) -> str:
        return '<br/>'
    
    @override
    def is_text(self) -> bool:
        return True

class RenderMessageData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]
    content: NotRequired['Message']

@dataclass
class RenderMessage(MessageSegment):
    data: RenderMessageData = field(default_factory=dict) # type: ignore
    
    @override
    def __str__(self) -> str:
        attr = []
        if 'id' in self.data:
            attr.append(f' id="{escape(self.data["id"])}"')
        if self.data.get('forward'):
            attr.append(' forward')
        if 'content' not in self.data:
            return f'<{self.type}{"".join(attr)}/>'
        else:
            return f'<{self.type}{"".join(attr)}>{self.data["content"]}</{self.type}>'

class QuoteData(TypedDict):
    content: 'Message'

@dataclass
class Quote(MessageSegment):
    data: QuoteData = field(default_factory=dict) # type: ignore
    
    @override
    def __str__(self) -> str:
        return f'<{self.type}>{self.data["content"]}</{self.type}>'

class AuthorData(TypedDict):
    id: str
    name: NotRequired[str]
    avatar: NotRequired[str]

@dataclass
class Author(MessageSegment):
    data: AuthorData = field(default_factory=dict) # type: ignore

class ButtonData(TypedDict):
    id: NotRequired[str]
    type: NotRequired[str]
    href: NotRequired[str]
    text: NotRequired[str]
    theme: NotRequired[str]

@dataclass
class Button(MessageSegment):
    data: ButtonData = field(default_factory=dict) # type: ignore

class PassiveData(TypedDict):
    id: NotRequired[str]
    seq: NotRequired[int]

@dataclass
class Passive(MessageSegment):
    data: PassiveData = field(default_factory=dict) # type: ignore

ELEMENT_TYPE_MAP = {
    'text': (Text, 'text'),
    'at': (At, 'at'),
    'sharp': (Sharp, 'sharp'),
    'img': (Img, 'img'),
    'image': (Img, 'img'),
    'audio': (Audio, 'audio'),
    'video': (Video, 'video'),
    'file': (File, 'file'),
    'author': (Author, 'author')
}

STYLE_TYE_MAP = {
    'b': 'b',
    'strong': 'b',
    'i': 'i',
    'em': 'i',
    'u': 'u',
    'ins': 'u',
    's': 's',
    'del': 's',
    'spl': 'spl',
    'code': 'code',
    'sup': 'sup',
    'sub': 'sub',
    'p': 'p'
}

class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment
    
    @override
    def __str__(self) -> str:
        text = ''.join(str(seg) for seg in self)
        
        def calc_depth(msg: 'Message') -> int:
            depth = 0
            for seg in msg:
                if seg.type == 'style':
                    depth = max(depth, len(seg.data['styles']))
                if seg.type == 'message' or seg.type == 'quote':
                    depth = max(depth, calc_depth(seg.data['content']))
            return depth
        
        pat = re.compile(r'</(\w+)(?<!/p)><\1>')
        for _ in range(calc_depth(self)):
            text = pat.sub('', text)
        return text
    
    @override
    def __add__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> 'Message':
        return super().__add__(MessageSegment.text(other) if isinstance(other, str) else other)
    
    @override
    def __radd__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> 'Message':
        return super().__radd__(MessageSegment.text(other) if isinstance(other, str) else other)
    
    @staticmethod
    @override
    def _construct(message: str) -> Iterable[MessageSegment]:
        yield from Message.from_satori_element(parse(message))
    
    @classmethod
    def from_satori_element(cls, elements: list[Element]) -> 'Message':
        message = Message()
        
        def handle(element: Element, upper_styles: Optional[list[str]] = None):
            tag = element.tag()
            if tag in ELEMENT_TYPE_MAP:
                seg_cls, seg_type = ELEMENT_TYPE_MAP[tag]
                yield seg_cls(seg_type, element.attrs.copy())
            elif tag in ('a', 'link'):
                yield A('a', {'text': element.attrs['href']})
            elif tag == 'button':
                yield Button('button', {**element.attrs}) # type: ignore
            elif tag in STYLE_TYE_MAP:
                style = STYLE_TYE_MAP[tag]
                for child in element.children:
                    child_tag = child.tag()
                    if child_tag == 'text':
                        yield Style(
                            'style', {'text': child.attrs['text'], 'styles': [*(upper_styles or []), style]}
                        )
                    else:
                        yield from handle(child, [*(upper_styles or []), style])
            elif tag in ('br', 'newline'):
                yield Br('br', {'text': '\n'})
            elif tag in ('message', 'quote'):
                data = element.attrs.copy()
                if element.children:
                    data['content'] = Message.from_satori_element(element.children)
                if tag == 'message':
                    yield RenderMessage('message', data) # type: ignore
                else:
                    yield Quote('quote', data) # type: ignore
        
        for element in elements:
            message.extend(handle(element))
        
        return message
    
    @override
    def extract_plain_text(self) -> str:
        return ''.join(seg.data['text'] for seg in self if seg.is_text())
