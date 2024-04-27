import re
from pathlib import Path
from base64 import b64encode
from dataclasses import InitVar, field, dataclass
from typing_extensions import override
from typing import (
    Any,
    NotRequired,
    Self,
    Type,
    Tuple,
    Union,
    Literal,
    Iterable,
    Optional,
    Generator,
    TypedDict,
    overload
)

from anonbot.adapter import SrcBase64, uni
from anonbot.adapter import Message as BaseMessage
from anonbot.adapter import MessageSegment as BaseMessageSegment

from .element import Element, parse, escape, param_case

def _parse_src(src: Union[str, Path, SrcBase64]) -> str:
    if isinstance(src, str):
        # 判断链接或路径
        if re.match(r'^https?://', src):
            return src
        else:
            return Path(src).absolute().as_uri()
    elif isinstance(src, Path):
        return src.absolute().as_uri()
    else:
        bytes_data = src['data'] if isinstance(src['data'], bytes) else src['data'].getvalue() # type: ignore
        return f'data:{src["type"]};base64,{b64encode(bytes_data).decode()}'

class MessageSegment(BaseMessageSegment['Message']):
    children: Optional['Message'] = None
    '''消息段子消息'''
    
    def __str__(self) -> str:
        def _attr(key: str, value: Any) -> str:
            if value is None:
                return ''
            key = param_case(key)
            if value is True:
                return f' {key}'
            if isinstance(value, str):
                return f' {key}="{escape(value, True)}"'
            else:
                return f' {key}="{escape(str(value), True)}"'
        
        attrs = ''.join(_attr(k, v) for k, v in self.data.items())
        if self.type == 'text' and 'text' in self.data:
            return escape(self.data['text'])
        if self.children is None:
            return f'<{self.type}{attrs}/>'
        else:
            return f'<{self.type}{attrs}>{str(self.children)}</{self.type}>'
    
    def __extra_attr__(self, *inner_attrs: str) -> str:
        def _attr(key: str, value: Any) -> str:
            if value is None:
                return ''
            key = param_case(key)
            if value is True:
                return f' {key}'
            if value is False:
                return f' no-{key}'
            return f' {key}="{escape(value, True)}"'
        
        attrs = ''.join(_attr(k, v) for k, v in self.data.items() if k not in inner_attrs)
        return f'{attrs}'
    
    @classmethod
    @override
    def get_message_class(cls) -> Type['Message']:
        return Message
    
    def set_children(self, children: Optional['Message'] = None) -> Self:
        self.children = children
        return self
    
    @staticmethod
    def text(text: str) -> 'Text':
        return Text('text', {'text': text, 'styles': {}})
    
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
    @overload
    def at(
        id: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        type: Optional[str] = None
    ) -> 'At': ...
    
    @staticmethod
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
    def sharp(id: str, name: Optional[str]=None) -> 'Sharp':
        data: SharpData = {'id': id}
        if name is not None:
            data['name'] = name
        return Sharp('sharp', data)
    
    @staticmethod
    def a(href: str) -> 'A':
        return A('a', {'href': href})
    
    @staticmethod
    def img(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> 'Img':
        data: ImgData = {'src': _parse_src(src)}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        if width is not None:
            data['width'] = width
        if height is not None:
            data['height'] = height
        return Img('img', data)
    
    @staticmethod
    def audio(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        duration: Optional[float] = None,
        poster: Optional[str] = None
    ) -> 'Audio':
        data: AudioData = {'src': _parse_src(src)}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        if duration is not None:
            data['duration'] = duration
        if poster is not None:
            data['poster'] = poster
        return Audio('audio', data)
    
    @staticmethod
    def video(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[float] = None,
        poster: Optional[str] = None
    ) -> 'Video':
        data: VideoData = {'src': _parse_src(src)}
        if title is not None:
            data['title'] = title
        if cache is not None:
            data['cache'] = cache
        if timeout is not None:
            data['timeout'] = timeout
        if width is not None:
            data['width'] = width
        if height is not None:
            data['height'] = height
        if duration is not None:
            data['duration'] = duration
        if poster is not None:
            data['poster'] = poster
        return Video('video', data)
    
    @staticmethod
    def file(
        src: Union[str, Path, SrcBase64],
        title: Optional[str] = None,
        cache: Optional[bool] = None,
        timeout: Optional[str] = None,
        poster: Optional[str] = None
    ) -> 'File':
        data: FileData = {'src': _parse_src(src)}
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
    def b(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['b']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'b')
        return text
    
    @staticmethod
    def i(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['i']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'i')
        return text
    
    @staticmethod
    def u(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['u']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'u')
        return text
    
    @staticmethod
    def s(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['s']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 's')
        return text
    
    @staticmethod
    def spl(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['spl']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'spl')
        return text
    
    @staticmethod
    def code(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['code']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'code')
        return text
    
    @staticmethod
    def sup(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['sup']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'sup')
        return text
    
    @staticmethod
    def sub(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['sub']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'sub')
        return text
    
    @staticmethod
    def br() -> 'Br':
        return Br('br', {'text': '\n'})
    
    @staticmethod
    def p(text: Union[str, 'Text']) -> 'Text':
        if isinstance(text, str):
            return Text('text', {'text': text, 'styles': {(0, len(text)): ['p']}})
        text.data['styles'].setdefault((0, len(text.data['text'])), []).insert(0, 'p')
        return text
    
    @staticmethod
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
            children = Message(message)
        else:
            children = None
        return RenderMessage('message', data).set_children(children) # type: ignore
    
    @staticmethod
    def quote(
        id: Optional[str]=None,
        forward: Optional[bool]=None,
        message: Optional[Union[str, 'MessageSegment', Iterable['MessageSegment']]]=None
    ) -> 'Quote':
        data = {}
        if id:
            data['id'] = id
        if forward is not None:
            data['forward'] = forward
        if message:
            children = Message(message)
        else:
            children = None
        return Quote('quote', data).set_children(children) # type: ignore
    
    @staticmethod
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
    def extend(type: str, **kwargs: Any) -> 'Extend':
        data = {}
        children = None
        for key, value in kwargs.items():
            if isinstance(value, (Message, MessageSegment)):
                children = Message(children) + value
            else:
                data[key] = value
        return Extend(type, data).set_children(children)
    
    @override
    def is_text(self) -> bool:
        return False

class TextData(TypedDict):
    text: str
    styles: dict[Tuple[int, int], list[str]]

@dataclass
class Text(MessageSegment):
    data: TextData = field(default_factory=dict) # type: ignore
    
    def __post_init__(self) -> None:
        if 'styles' not in self.data:
            self.data['styles'] = {}
    
    def __merge__(self) -> None:
        data: dict[int, list[str]] = {}
        styles = self.data['styles']
        if not styles:
            return
        for scale, _styles in styles.items():
            for i in range(*scale):
                if i not in data:
                    data[i] = _styles[:]
                else:
                    data[i].extend(_style for _style in _styles if _style not in data[i])
        styles.clear()
        data1: dict[str, list[int]] = {}
        for i, _styles in data.items():
            key = '\x01'.join(_styles)
            data1.setdefault(key, []).append(i)
        data.clear()
        data2: dict[Tuple[int, int], list[str]] = {}
        for key, indexes in data1.items():
            start = indexes[0]
            end = start
            for i in indexes[1:]:
                if i - end == 1:
                    end = i
                else:
                    data2[(start, end + 1)] = key.split('\x01')
                    start = end = i
            if end >= start:
                data2[(start, end + 1)] = key.split('\x01')
        for scale in sorted(data2.keys()):
            styles[scale] = data2[scale]
    
    def mark(self, start: int, end: int, *styles: str) -> Self:
        _styles = self.data['styles'].setdefault((start, end), [])
        for style in styles:
            style = STYLE_TYPE_MAP.get(style, style)
            if style not in _styles:
                _styles.append(style)
        self.__merge__()
        return self
    
    @override
    def __str__(self) -> str:
        result: list[str] = []
        text = self.data['text']
        styles = self.data['styles']
        if not styles:
            return escape(self.data['text'])
        self.__merge__()
        scales = sorted(styles.keys(), key=lambda x: x[0])
        left = scales[0][0]
        result.append(escape(text[:left]))
        for scale in scales:
            prefix = ''.join(f'<{style}>' for style in styles[scale])
            suffix = ''.join(f'</{style}>' for style in reversed(styles[scale]))
            result.append(prefix + escape(text[scale[0]:scale[1]]) + suffix)
        right = scales[-1][1]
        result.append(escape(text[right:]))
        text = ''.join(result)
        pat = re.compile(r'</(\w+)(?<!/p)><\1>')
        for _ in range(max(map(len, styles.values()))):
            text = pat.sub('', text)
        return text
    
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
    href: str

class A(MessageSegment):
    data: AData = field(default_factory=dict) # type: ignore
    
    @override
    def is_text(self) -> bool:
        return True

class SrcData(TypedDict):
    src: str
    title: NotRequired[str]
    cache: NotRequired[bool]
    timeout: NotRequired[str]

class ImgData(SrcData, total=False):
    width: NotRequired[int]
    height: NotRequired[int]

@dataclass
class Img(MessageSegment):
    data: ImgData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class AudioData(SrcData, total=False):
    duration: NotRequired[float]
    poster: NotRequired[str]

@dataclass
class Audio(MessageSegment):
    data: AudioData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class VideoData(SrcData, total=False):
    width: NotRequired[int]
    height: NotRequired[int]
    duration: NotRequired[float]
    poster: NotRequired[str]

@dataclass
class Video(MessageSegment):
    data: VideoData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class FileData(SrcData, total=False):
    poster: NotRequired[str]

@dataclass
class File(MessageSegment):
    data: FileData = field(default_factory=dict) # type: ignore
    extra: InitVar[Optional[dict[str, Any]]] = None
    
    def __post_init__(self, extra: Optional[dict[str, Any]]) -> None:
        if extra is not None:
            self.data.update(extra) # type: ignore

class Br(MessageSegment):
    
    @override
    def is_text(self) -> bool:
        return True

class RenderMessageData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]

@dataclass
class RenderMessage(MessageSegment):
    data: RenderMessageData = field(default_factory=dict) # type: ignore
    
class QuoteData(TypedDict):
    id: NotRequired[str]
    forward: NotRequired[bool]

@dataclass
class Quote(MessageSegment):
    data: QuoteData = field(default_factory=dict) # type: ignore

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
class Extend(MessageSegment):
    data: dict[str, Any] = field(default_factory=dict)
    
    @override
    def is_text(self) -> bool:
        if self.children:
            return False
        if len(self.data) == 1:
            for value in self.data.values():
                return isinstance(value, str)
        return False

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

STYLE_TYPE_MAP = {
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

def handle(element: Element, upper_style: Optional[list[str]] = None) -> Generator[Any, None, None]:
    tag = element.tag()
    if len(element.children) > 0:
        children = Message.from_satori_element(element.children)
    else:
        children = None
    if tag in ELEMENT_TYPE_MAP:
        seg_cls, seg_type = ELEMENT_TYPE_MAP[tag]
        yield seg_cls(seg_type, element.attrs.copy()).set_children(children)
    elif tag in ('a', 'link'):
        attrs = element.attrs.copy()
        yield A('a', attrs | {'href': attrs.get('href', '')}).set_children(children)
    elif tag in STYLE_TYPE_MAP:
        style = STYLE_TYPE_MAP[tag]
        for child in element.children:
            child_tag = child.tag()
            if child_tag == 'text':
                yield Text(
                    'text',
                    {
                        'text': child.attrs['text'],
                        'styles': {(0, len(child.attrs['text'])): [*(upper_style or []), style]}
                    }
                )
            else:
                yield from handle(child, [*(upper_style or []), style])
    elif tag in ('br', 'newline'):
        yield Br('br', {'text': '\n'}).set_children(children)
    elif tag in ('message', 'quote'):
        data = element.attrs.copy()
        if tag == 'message':
            yield RenderMessage('message', data).set_children(children) # type: ignore
        else:
            yield Quote('quote', data).set_children(children) # type: ignore
    else:
        data = element.attrs.copy()
        yield Extend(element.tag(), data).set_children(children)

class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment
    
    @override
    def __add__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> 'Message':
        return super().__add__(MessageSegment.text(other) if isinstance(other, str) else other).__merge_text__()
    
    @override
    def __radd__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> 'Message':
        return super().__radd__(MessageSegment.text(other) if isinstance(other, str) else other).__merge_text__()
    
    @staticmethod
    @override
    def _construct(message: str) -> Iterable[MessageSegment]:
        yield from Message.from_satori_element(parse(message))
    
    @classmethod
    def from_satori_element(cls, elements: list[Element]) -> 'Message':
        message = Message()
        
        for element in elements:
            message.extend(handle(element))
        
        return message.__merge_text__()
    
    @override
    def extract_plain_text(self) -> str:
        return ''.join(seg.data['text'] for seg in self if seg.is_text())

    def __merge_text__(self) -> Self:
        if not self:
            return self
        result = []
        last = self[0]
        for seg in self[1:]:
            if last.type == 'text' and seg.type == 'text':
                assert isinstance(last, Text)
                _len = len(last.data['text'])
                last.data['text'] += seg.data['text']
                for scale, styles in seg.data['styles'].items():
                    last.data['styles'][(scale[0] + _len, scale[1] + _len)] = styles[:]
            else:
                result.append(last)
                last = seg
        result.append(last)
        self.clear()
        self.extend(result)
        return self

    @staticmethod
    @override
    def parse_uni_message(uni_message: uni.Message) -> 'Message':
        msg = Message()
        for seg in uni_message:
            match seg.type:
                case 'text':
                    msg += MessageSegment.text(seg.text)
                case 'at':
                    _seg = MessageSegment.at(
                        id=seg.data.get('id', None),
                        name=seg.data.get('name', None),
                        role=seg.data.get('role', None),
                        type=seg.data.get('type', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'sharp':
                    _seg = MessageSegment.sharp(seg.data['id'], seg.data.get('name', None))
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'link':
                    _seg = MessageSegment.a(seg.data['href'])
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'image':
                    _seg = MessageSegment.img(
                        src=seg.data['src'],
                        title=seg.data.get('title', None),
                        cache=seg.data.get('cache', None),
                        timeout=seg.data.get('timeout', None),
                        width=seg.data.get('width', None),
                        height=seg.data.get('height', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'audio':
                    _seg = MessageSegment.audio(
                        src=seg.data['src'],
                        title=seg.data.get('title', None),
                        cache=seg.data.get('cache', None),
                        timeout=seg.data.get('timeout', None),
                        duration=seg.data.get('duration', None),
                        poster=seg.data.get('poster', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'video':
                    _seg = MessageSegment.video(
                        src=seg.data['src'],
                        title=seg.data.get('title', None),
                        cache=seg.data.get('cache', None),
                        timeout=seg.data.get('timeout', None),
                        width=seg.data.get('width', None),
                        height=seg.data.get('height', None),
                        duration=seg.data.get('duration', None),
                        poster=seg.data.get('poster', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'file':
                    _seg = MessageSegment.file(
                        src=seg.data['src'],
                        title=seg.data.get('title', None),
                        cache=seg.data.get('cache', None),
                        timeout=seg.data.get('timeout', None),
                        poster=seg.data.get('poster', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'style':
                    msg += Text('text', {'text': seg.text, 'styles': {(0, len(seg.text)): [seg.style]}})
                case 'br':
                    msg += MessageSegment.br()
                case 'message':
                    _seg = MessageSegment.message(
                        id=seg.data.get('id', None),
                        forward=seg.data.get('forward', None),
                        message=Message.parse_uni_message(seg.children) if seg.children is not None else None
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    msg += _seg
                case 'quote':
                    _seg = MessageSegment.message(
                        id=seg.data.get('id', None),
                        forward=seg.data.get('forward', None),
                        message=Message.parse_uni_message(seg.children) if seg.children is not None else None
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    msg += _seg
                case 'author':
                    _seg = MessageSegment.author(
                        id=seg.data['id'],
                        name=seg.data.get('name', None),
                        avatar=seg.data.get('avatar', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case 'button':
                    _seg = MessageSegment.button(
                        id=seg.data.get('id', None),
                        type=seg.data.get('type', None),
                        href=seg.data.get('href', None),
                        text=seg.data.get('text', None),
                        theme=seg.data.get('theme', None)
                    )
                    _seg.data = seg.data | _seg.data # type: ignore
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
                case _:
                    _seg = MessageSegment.extend(seg.type)
                    _seg.data = seg.data.copy()
                    if seg.children is not None:
                        _seg.set_children(Message.parse_uni_message(seg.children))
                    msg += _seg
        
        return msg
