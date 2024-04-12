'''用于跨平台互通的 UniMessage
所有适配器都需要基于此进行实现
'''
from io import BytesIO
from pathlib import Path
from copy import deepcopy
from typing_extensions import override
from types import MethodType, FunctionType
from typing import TYPE_CHECKING, Any, Type, Union, Callable, Iterable, Optional

from anonbot.internal.adapter.message import Message as BaseMessage

from .segment import (
    At,
    Br,
    File,
    Link,
    Text,
    Audio,
    Image,
    Other,
    Quote,
    Sharp,
    Style,
    Video,
    Author,
    Button,
    SrcBase64,
    RenderMessage,
    MessageSegment
)

class chainedmethod:
    def __init__(self, function: FunctionType) -> None:
        self.__func__ = function
    
    def __get__(self, instance: Any, owner: Type[Any]) -> Union[MethodType, FunctionType]:
        if instance is None:
            return self.__func__.__get__(owner, owner)
        return self.__func__.__get__(instance, owner)

class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> type[MessageSegment]:
        return MessageSegment
    
    @override
    def __str__(self) -> str:
        return ''.join(str(seg) for seg in self)
    
    @override
    def __add__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> 'Message':
        return super().__add__(Text(other) if isinstance(other, str) else other)
    
    @override
    def __radd__(self, other: Union[str, MessageSegment, Iterable[MessageSegment]]) -> 'Message':
        return super().__radd__(Text(other) if isinstance(other, str) else other)
    
    def __getattr__(self, name) -> Callable[..., 'Message']:
        def _type(**kwargs: Any) -> 'Message':
            return self.other(name, **kwargs)
        return _type
    
    def __deepcopy__(self, memo) -> 'Message':
        _new_message = Message()
        _new_message.extend([deepcopy(seg) for seg in self])
        return _new_message
    
    @staticmethod
    @override
    def _construct(message: str) -> Iterable[MessageSegment]:
        return Message(Text(message))
    
    @override
    def extract_plain_text(self) -> str:
        return ''.join(seg.data['text'] for seg in self if seg.is_text())

    if TYPE_CHECKING:
        @classmethod
        def at(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            id: Optional[str]=None,
            name: Optional[str]=None,
            role: Optional[str]=None,
            type: Optional[str]=None
        ) -> 'Message':
            '''提及用户

            参数:
                id (Optional[str], optional): 目标用户的 ID
                name (Optional[str], optional): 目标用户的名称
                role (Optional[str], optional): 目标角色
                type (Optional[str], optional): 特殊操作
            '''
            ...
        
        @classmethod
        def br(cls_or_self: Union['Message', Type['Message']]) -> 'Message': # type: ignore
            '''换行'''
            ...
        
        @classmethod
        def file(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            src: Union[str, Path, SrcBase64],
            name: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            poster: Optional[str] = None
        ) -> 'Message':
            '''文件

            参数:
                src (Union[str, Path, SrcBase64]): 资源的 URL 或文件路径或二进制数据
                name (Optional[str], optional): 资源文件名称
                cache (Optional[bool], optional): 是否使用已缓存的文件
                timeout (Optional[str], optional): 下载文件的最长时间 (毫秒)
                poster (Optional[str], optional): 缩略图 URL
            '''
            ...
        
        @classmethod
        def link(cls_or_self: Union['Message', Type['Message']], href: str) -> 'Message': # type: ignore
            '''链接

            参数:
                href (str): 链接的 URL
            '''
            ...
        
        @classmethod
        def text(cls_or_self: Union['Message', Type['Message']], text: str) -> 'Message': # type: ignore
            '''一段纯文本

            参数:
                text (str): 文本内容
            '''
            ...
        
        @classmethod
        def audio(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            src: Union[str, Path, SrcBase64],
            title: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            duration: Optional[float] = None,
            poster: Optional[str] = None
        ) -> 'Message':
            '''音频

            参数:
                src (Union[str, Path, SrcBase64]): 资源的 URL 或文件路径或二进制数据
                title (Optional[str], optional): 资源文件名称
                cache (Optional[bool], optional): 是否使用已缓存的文件
                timeout (Optional[str], optional): 下载文件的最长时间 (毫秒)
                duration (Optional[float], optional): 音频长度 (秒)
                poster (Optional[str], optional): 音频封面 URL
            '''
            ...
        
        @classmethod
        def image(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            src: Union[str, Path, SrcBase64],
            title: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            width: Optional[int] = None,
            height: Optional[int] = None
        ) -> 'Message':
            '''图片

            参数:
                src (Union[str, Path, SrcBase64]): 资源的 URL 或文件路径或二进制数据
                title (Optional[str], optional): 资源文件名称
                cache (Optional[bool], optional): 是否使用已缓存的文件
                timeout (Optional[str], optional): 下载文件的最长时间 (毫秒)
                width (Optional[int], optional): 图片宽度 (像素)
                height (Optional[int], optional): 图片高度 (像素)
            '''
            ...
        
        @classmethod
        def other(cls_or_self: Union['Message', Type['Message']], type: str, **kwargs: Any) -> 'Message': # type: ignore
            '''其他类型的消息段

            参数:
                type (str): 消息段类型
                **kwargs: 消息段字段
            '''
            ...
        
        @classmethod
        def quote(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            content: Union[str, MessageSegment, 'Message']
        ) -> 'Message':
            '''引用

            参数:
                content (Message): 子元素
            '''
            ...
        
        @classmethod
        def sharp(cls_or_self: Union['Message', Type['Message']], id: str, name: Optional[str] = None) -> 'Message': # type: ignore
            '''提及频道

            参数:
                id (str): 目标频道的 ID
                name (Optional[str], optional): 目标频道的名称
            '''
            ...
        
        @classmethod
        def style(cls_or_self: Union['Message', Type['Message']], text: str, style: str) -> 'Message': # type: ignore
            '''修饰样式

            参数:
                text (str): 文本内容
                style (str): 修饰样式种类
            '''
            ...
        
        @classmethod
        def video(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            src: Union[str, Path, SrcBase64],
            title: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            duration: Optional[float] = None,
            poster: Optional[str] = None
        ) -> 'Message':
            '''视频

            参数:
                src (Union[str, Path, SrcBase64]): 资源的 URL 或文件路径或二进制数据
                title (Optional[str], optional): 资源文件名称
                cache (Optional[bool], optional): 是否使用已缓存的文件
                timeout (Optional[str], optional): 下载文件的最长时间 (毫秒)
                width (Optional[int], optional): 视频宽度 (像素)
                height (Optional[int], optional): 视频高度 (像素)
                duration (Optional[float], optional): 视频长度 (秒)
                poster (Optional[str], optional): 视频封面 URL
            '''
            ...
        
        @classmethod
        def author(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            id: Optional[str] = None,
            name: Optional[str] = None,
            avatar: Optional[str] = None
        ) -> 'Message':
            '''作者

            参数:
                id (Optional[str], optional): 用户 ID
                name (Optional[str], optional): 昵称
                avatar (Optional[str], optional): 头像 URL
            '''
            ...
        
        @classmethod
        def button(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            id: Optional[str] = None,
            type: Optional[str] = None,
            href: Optional[str] = None,
            text: Optional[str] = None,
            theme: Optional[str] = None
        ) -> 'Message':
            '''按钮

            参数:
                id (Optional[str], optional): 按钮的 ID
                type (Optional[str], optional): 按钮的类型
                href (Optional[str], optional): 按钮的链接
                text (Optional[str], optional): 待输入文本
                theme (Optional[str], optional): 按钮的样式
            '''
            ...
        
        @classmethod
        def message(
            cls_or_self: Union['Message', Type['Message']], # type: ignore
            id: Optional[str] = None,
            forward: Optional[bool] = None,
            content: Optional[Union[str, MessageSegment, 'Message']] = None
        ) -> 'Message':
            '''消息

            参数:
                id (Optional[str], optional): 消息的 ID
                forward (Optional[bool], optional): 是否为转发消息
                content (Optional[Message], optional): 子元素
            '''
            ...
    
    else:
        @chainedmethod
        def at(
            cls_or_self,
            id: Optional[str]=None,
            name: Optional[str]=None,
            role: Optional[str]=None,
            type: Optional[str]=None
        ) -> 'Message':
            at = At(id, name, role, type)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(at)
            return Message(at)
        
        @chainedmethod
        def br(cls_or_self) -> 'Message':
            br = Br()
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(br)
            return Message(br)
        
        @chainedmethod
        def file(
            cls_or_self,
            src: Union[str, Path, SrcBase64],
            name: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            poster: Optional[str] = None
        ) -> 'Message':
            file = File(src, name, cache, timeout, poster)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(file)
            return Message(file)
        
        @chainedmethod
        def link(cls_or_self, href: str) -> 'Message':
            link = Link(href)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(link)
            return Message(link)
        
        @chainedmethod
        def text(cls_or_self, text: str) -> 'Message':
            text = Text(text)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(text)
            return Message(text)
        
        @chainedmethod
        def audio(
            cls_or_self,
            src: Union[str, Path, BytesIO],
            title: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            duration: Optional[float] = None,
            poster: Optional[str] = None
        ) -> 'Message':
            audio = Audio(src, title, cache, timeout, duration, poster)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(audio)
            return Message(audio)
        
        @chainedmethod
        def image(
            cls_or_self,
            src: Union[str, Path, BytesIO],
            title: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            width: Optional[int] = None,
            height: Optional[int] = None
        ) -> 'Message':
            image = Image(src, title, cache, timeout, width, height)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(image)
            return Message(image)
        
        @chainedmethod
        def other(cls_or_self, type: str, **kwargs: Any) -> 'Message':
            other = Other(type, **kwargs)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(other)
            return Message(other)
        
        @chainedmethod
        def quote(cls_or_self, content: Union[str, MessageSegment, 'Message']) -> 'Message':
            quote = Quote(content)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(quote)
            return Message(quote)
        
        @chainedmethod
        def sharp(cls_or_self, id: str, name: Optional[str] = None) -> 'Message':
            sharp = Sharp(id, name)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(sharp)
            return Message(sharp)
        
        @chainedmethod
        def style(cls_or_self, text: str, style: str) -> 'Message':
            style = Style(text, style)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(style)
            return Message(style)
        
        @chainedmethod
        def video(
            cls_or_self,
            src: Union[str, Path, BytesIO],
            title: Optional[str] = None,
            cache: Optional[bool] = None,
            timeout: Optional[str] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            duration: Optional[float] = None,
            poster: Optional[str] = None
        ) -> 'Message':
            video = Video(src, title, cache, timeout, width, height, duration, poster)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(video)
            return Message(video)
        
        @chainedmethod
        def author(
            cls_or_self,
            id: Optional[str] = None,
            name: Optional[str] = None,
            avatar: Optional[str] = None
        ) -> 'Message':
            author = Author(id, name, avatar)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(author)
            return Message(author)
        
        @chainedmethod
        def button(
            cls_or_self,
            id: Optional[str] = None,
            type: Optional[str] = None,
            href: Optional[str] = None,
            text: Optional[str] = None,
            theme: Optional[str] = None
        ) -> 'Message':
            button = Button(id, type, href, text, theme)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(button)
            return Message(button)
        
        @chainedmethod
        def message(
            cls_or_self,
            id: Optional[str] = None,
            forward: Optional[bool] = None,
            content: Optional[Union[str, MessageSegment, 'Message']] = None
        ) -> 'Message':
            render_message = RenderMessage(id, forward, content)
            if isinstance(cls_or_self, Message):
                return cls_or_self.append(render_message)
            return Message(render_message)
