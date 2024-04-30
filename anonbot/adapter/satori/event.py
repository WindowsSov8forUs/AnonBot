from copy import deepcopy
from datetime import datetime
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Self, Type, Union, TypeVar, Optional

from pydantic import model_validator

from anonbot.adapter import uni
from anonbot.adapter import Event as BaseEvent

from .element import parse
from .models import Role, User
from .message import Message, Quote
from .models import Event as SatoriEvent
from .message import Button as ButtonMessage
from .models import InnerMessage as SatoriMessage
from .models import (
    Argv,
    Guild,
    Login,
    Button,
    Channel,
    EventType,
    ChannelType,
    InnerMember
)
from .message import (
    Text,
    At,
    Sharp,
    A,
    Img,
    Audio,
    Video,
    File,
    Author,
    Quote
)

E = TypeVar('E', bound='Event')

class Event(BaseEvent, SatoriEvent):
    __type__: EventType
    
    @override
    def get_id(self) -> int:
        return self.id
    
    @override
    def get_event_type(self) -> EventType:
        return EventType(self.type)
    
    @override
    def get_platform(self) -> str:
        return self.platform
    
    @override
    def get_self_id(self) -> str:
        return self.self_id
    
    @override
    def get_timestamp(self) -> datetime:
        return self.timestamp
    
    @override
    def get_argv(self) -> Optional[Argv]:
        return self.argv
    
    @override
    def get_button(self) -> Optional[Button]:
        return self.button
    
    @override
    def get_channel(self) -> Optional[Channel]:
        return self.channel
    
    @override
    def get_guild(self) -> Optional[Guild]:
        return self.guild
    
    @override
    def get_login(self) -> Optional[Login]:
        return self.login
    
    @override
    def get_member(self) -> Optional[InnerMember]:
        return self.member
    
    @override
    def get_message_data(self) -> Optional[SatoriMessage]:
        return self.message
    
    @override
    def get_operator(self) -> Optional[User]:
        return self.operator
    
    @override
    def get_role(self) -> Optional[Role]:
        return self.role
    
    @override
    def get_user(self) -> Optional[User]:
        return self.user
    
    @override
    def get_origin_type(self) -> Optional[str]:
        return self._type
    
    @override
    def get_origin_data(self) -> Optional[dict[str, Any]]:
        return self._data
    
    @override
    def get_uni_message(self) -> uni.Message:
        raise ValueError('Event has no message!')
    
    @override
    def get_type(self) -> Union[EventType, str]:
        return self.get_event_type()
    
    @override
    def get_event_name(self) -> str:
        return str(self.get_event_type())
    
    @override
    def get_event_description(self) -> str:
        return str(self.model_dump(exclude_none=True, exclude_unset=True))
    
    @override
    def get_message(self) -> Message:
        raise ValueError('Event has no message!')
    
    @override
    def get_user_id(self) -> str:
        if self.user:
            return self.user.id
        raise ValueError('Event has no context!')
    
    @override
    def get_session_id(self) -> str:
        if self.user:
            if self.channel:
                if self.guild:
                    return f'{self.guild.id}:{self.user.id}'
                return f'{self.channel.id}:{self.user.id}'
        else:
            if self.channel:
                return f'channel:{self.channel.id}'
            elif self.guild:
                return f'guild:{self.guild.id}'
        raise ValueError('Event has no context!')
    
    @override
    def is_tome(self) -> bool:
        return False

EVENT_CLASSES: dict[str, Type[Event]] = {}

def register_event_class(event_class: Type[E]) -> Type[E]:
    '''注册事件类'''
    EVENT_CLASSES[event_class.__type__.value] = event_class
    return event_class

class GuildEvent(Event):
    guild: Guild
    
    @override
    def get_guild(self) -> Guild:
        return self.guild
    
    @override
    def get_session_id(self) -> str:
        return f'guild:{self.guild.id}'

@register_event_class
class GuildAddedEvent(GuildEvent):
    __type__ = EventType.GUILD_ADDED

@register_event_class
class GuildUpdatedEvent(GuildEvent):
    __type__ = EventType.GUILD_UPDATED

@register_event_class
class GuildRemovedEvent(GuildEvent):
    __type__ = EventType.GUILD_REMOVED

@register_event_class
class GuildRequestEvent(GuildEvent):
    __type__ = EventType.GUILD_REQUEST

class GuildMemberEvent(GuildEvent):
    member: InnerMember
    user: User
    
    @override
    def get_member(self) -> InnerMember:
        return self.member
    
    @override
    def get_user(self) -> User:
        return self.user
    
    @override
    def get_user_id(self) -> str:
        return self.user.id
    
    @override
    def get_session_id(self) -> str:
        return f'{self.guild.id}:{self.get_user_id()}'

@register_event_class
class GuildMemberAddedEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_ADDED

@register_event_class
class GuildMemberUpdatedEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_UPDATED

@register_event_class
class GuildMemberRemovedEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_REMOVED

@register_event_class
class GuildMemberRequestEvent(GuildMemberEvent):
    __type__ = EventType.GUILD_MEMBER_REQUEST

class GuildRoleEvent(GuildEvent):
    role: Role
    
    @override
    def get_role(self) -> Role:
        return self.role
    
    @override
    def get_session_id(self) -> str:
        return f'{self.guild.id}:{self.role.id}'

@register_event_class
class GuildRoleCreatedEvent(GuildRoleEvent):
    __type__ = EventType.GUILD_ROLE_CREATED

@register_event_class
class GuildRoleUpdatedEvent(GuildRoleEvent):
    __type__ = EventType.GUILD_ROLE_UPDATED

@register_event_class
class GuildRoleDeletedEvent(GuildRoleEvent):
    __type__ = EventType.GUILD_ROLE_DELETED

class InteractionEvent(Event):
    @override
    def is_tome(self) -> bool:
        return True

@register_event_class
class InteractionButtonEvent(InteractionEvent):
    __type__ = EventType.INTERACTION_BUTTON
    
    button: Button
    
    @override
    def get_button(self) -> Button:
        return self.button
    
    @override
    def get_event_description(self) -> str:
        return f'Button interacted: {self.button.id}'

@register_event_class
class InteractionCommandEvent(InteractionEvent):
    __type__ = EventType.INTERACTION_COMMAND
    
    if TYPE_CHECKING:
        _message: Message
        original_message: Message
    
    @override
    def get_message(self) -> Message:
        return self._message
    
    def convert(self) -> 'InteractionCommandEvent':
        '''转换事件类型'''
        if self.argv:
            return InteractionCommandArgvEvent.model_validate(self.model_dump()) # type: ignore
        return InteractionCommandMessageEvent.model_validate(self.model_dump()) # type: ignore

class InteractionCommandArgvEvent(InteractionCommandEvent):
    argv: Argv
    
    @override
    def get_argv(self) -> Argv:
        return self.argv
    
    @override
    def get_event_description(self) -> str:
        return f'Command interacted: {self.argv}'
    
    @model_validator(mode='after')
    def generate_message(self) -> Self:
        argv: Argv = self.argv
        cmd = argv.name
        if argv.arguments:
            cmd += ' ' + ' '.join(argv.arguments)
            self._message = Message(cmd)
            self.original_message = deepcopy(self._message)
        return self

class InteractionCommandMessageEvent(InteractionCommandEvent):
    message: SatoriMessage
    to_me: bool = False
    reply: Optional[Quote] = None
    
    @override
    def get_message_data(self) -> SatoriMessage:
        return self.message
    
    @override
    def get_event_description(self) -> str:
        return f'Command interacted: {self.get_message()}'
    
    @model_validator(mode='after')
    def generate_message(self) -> Self:
        self._message = Message.from_satori_element(parse(self.message.content))
        self.original_message = deepcopy(self._message)
        return self

class LoginEvent(Event):
    login: Login

@register_event_class
class LoginAddedEvent(LoginEvent):
    __type__ = EventType.LOGIN_ADDED

@register_event_class
class LoginUpdatedEvent(LoginEvent):
    __type__ = EventType.LOGIN_UPDATED

@register_event_class
class LoginRemovedEvent(LoginEvent):
    __type__ = EventType.LOGIN_REMOVED

class MessageEvent(Event):
    channel: Channel
    message: SatoriMessage
    user: User
    to_me: bool = False
    reply: Optional[Quote] = None
    
    if TYPE_CHECKING:
        _message: Message
        original_message: Message
    
    @override
    def get_channel(self) -> Channel:
        return self.channel
    
    @override
    def get_message_data(self) -> SatoriMessage:
        return self.message
    
    @override
    def get_uni_message(self) -> uni.Message:
        return self._to_uni_message(self.get_message())
    
    @staticmethod
    def _to_uni_message(message: Message) -> uni.Message:
        msg = uni.Message()
        for seg in message:
            match seg.type:
                case 'text':
                    msg = msg.text(seg.data['text'])
                case 'at':
                    msg = msg.at()
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
                case 'sharp':
                    msg = msg.sharp(seg.data['id'])
                    for key, value in seg.data.items():
                        if key != 'id':
                            msg = msg.set_attr(key, value)
                case 'a':
                    msg = msg.link(seg.data['href'])
                    for key, value in seg.data.items():
                        if key != 'href':
                            msg = msg.set_attr(key, value)
                case 'img':
                    msg = msg.image(seg.data['src'])
                    for key, value in seg.data.items():
                        if key != 'src':
                            msg = msg.set_attr(key, value)
                case 'audio':
                    msg = msg.audio(seg.data['src'])
                    for key, value in seg.data.items():
                        if key != 'src':
                            msg = msg.set_attr(key, value)
                case 'video':
                    msg = msg.video(seg.data['src'])
                    for key, value in seg.data.items():
                        if key != 'src':
                            msg = msg.set_attr(key, value)
                case 'file':
                    msg = msg.file(seg.data['src'])
                    for key, value in seg.data.items():
                        if key != 'src':
                            msg = msg.set_attr(key, value)
                case 'br':
                    msg = msg.br()
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
                case 'message':
                    msg = msg.message()
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
                case 'quote':
                    msg = msg.quote()
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
                case 'author':
                    msg = msg.author()
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
                case 'button':
                    msg = msg.button()
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
                case _:
                    msg = msg.other(seg.type)
                    for key, value in seg.data.items():
                        msg = msg.set_attr(key, value)
            
            if seg.children:
                children = MessageEvent._to_uni_message(seg.children)
                msg.set_children(children)
        
        return msg
    
    @override
    def get_user(self) -> User:
        return self.user
    
    @override
    def is_tome(self) -> bool:
        return self.to_me
    
    @override
    def get_message(self) -> Message:
        return self._message
    
    @model_validator(mode='after')
    def generate_message(self) -> Self:
        self._message = Message.from_satori_element(parse(self.message.content))
        self.original_message = deepcopy(self._message)
        return self
    
    @property
    def message_id(self) -> str:
        return self.message.id

@register_event_class
class MessageCreatedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_CREATED
    
    @override
    def get_log_string(self) -> str:
        log_string = ''
        
        # 添加来源信息
        from_infos = []
        user = self.get_user()
        member = self.get_member()
        channel = self.get_channel()
        if guild := self.guild:
            if guild.id != channel.id:
                from_infos.append(f'{guild.name}({guild.id})')
        if channel.type != ChannelType.DIRECT:
            from_infos.append(f'{channel.name}({channel.id})')
        from_infos.append(
            f'{member.nick if member and member.nick else user.name}'
            f'({user.id})'
        )
        log_string += '-'.join(from_infos) + ': '
        # 添加消息信息
        messages: list[str] = []
        for segment in self.original_message:
            if isinstance(segment, Text):
                messages.append(segment.data['text'].replace('\r', ''))
            elif isinstance(segment, A):
                messages.append(segment.data['href'].replace('\r', ''))
            elif isinstance(segment, At):
                if segment.data.get('type', None) is None and segment.data.get('role', None) is None:
                    messages.append(f'@{segment.data.get("name", "None")}({str(segment.data.get("id", 0))}) ')
                elif segment.data.get('type', None) is not None:
                    if (type := segment.data.get('type', None)) != 'all':
                        messages.append(f'@{type} ')
                    else:
                        messages.append('@全体成员 ')
                else:
                    messages.append(f'@{segment.data.get("role", None)} ')
            elif isinstance(segment, Sharp):
                messages.append(f'#{segment.data.get("id", None)}({segment.data["id"]}) ')
            elif isinstance(segment, Img):
                messages.append(f'[图片]({segment.data["src"]})')
            elif isinstance(segment, Audio):
                messages.append(f'[音频]({segment.data["src"]})')
            elif isinstance(segment, Video):
                messages.append(f'[视频]({segment.data["src"]})')
            elif isinstance(segment, File):
                messages.append(f'[文件]({segment.data["src"]})')
            elif isinstance(segment, Message):
                messages.append('[转发消息]')
            elif isinstance(segment, Author):
                messages.append(f'[{segment.data.get("name", None)}({segment.data.get("id", None)})]')
            elif isinstance(segment, Quote):
                if segment.children is not None:
                    _content = segment.children.get('author', 1)
                    _seg = _content[0] if len(_content) > 0 else None
                    _author: Optional[Author] = _seg if isinstance(_seg, Author) else None
                else:
                    _author = None
                messages.append(f'[回复{_author.data["id"] if _author else ""}] ')
            elif isinstance(segment, ButtonMessage):
                messages.append(f'[按钮]')
            else:
                messages.append(f'[{segment.type}]')
        log_string += ''.join(messages)
        
        return log_string

@register_event_class
class MessageUpdatedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_UPDATED

@register_event_class
class MessageDeletedEvent(MessageEvent):
    __type__ = EventType.MESSAGE_DELETED
    
    @override
    def get_log_string(self) -> str:
        user_info = f'{self.user.name}({self.user.id})'
        return f'{user_info}撤回了一条消息: {self.message_id}'

class ReactionEvent(Event):
    channel: Channel
    message: SatoriMessage
    user: User
    
    if TYPE_CHECKING:
        _message: Message
    
    @override
    def get_channel(self) -> Channel:
        return self.channel
    
    @override
    def get_message_data(self) -> SatoriMessage:
        return self.message
    
    @override
    def get_user(self) -> User:
        return self.user
    
    @override
    def get_user_id(self) -> str:
        return self.user.id
    
    @override
    def get_session_id(self) -> str:
        if self.guild:
            return f'{self.guild.id}:{self.get_user_id()}'
        else:
            return f'{self.channel.id}:{self.get_user_id()}'
    
    @model_validator(mode='after')
    def generate_message(self) -> Self:
        self._message = Message.from_satori_element(parse(self.message.content))
        return self
    
    @property
    def message_id(self) -> str:
        return self.message.id

@register_event_class
class ReactionAddedEvent(ReactionEvent):
    __type__ = EventType.REACTION_ADDED
    
    @override
    def get_event_description(self) -> str:
        return f'Reaction added: {self.message_id} by {self.user.name}({self.channel.id})'

@register_event_class
class ReactionRemovedEvent(ReactionEvent):
    __type__ = EventType.REACTION_REMOVED
    
    @override
    def get_event_description(self) -> str:
        return f'Reaction removed: {self.message_id}'

@register_event_class
class InternalEvent(Event):
    __type__ = EventType.INTERNAL

    @override
    def get_event_name(self) -> str:
        return getattr(self, '_type', 'internal')
