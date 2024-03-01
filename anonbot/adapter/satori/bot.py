import json
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Type, Union, Optional

from anonbot.message import handle_event
from anonbot.driver import Request, Response

from anonbot.adapter import Bot as BaseBot

from .config import ClientInfo
from .event import Event, MessageEvent
from .message import Message, MessageSegment
from .models import InnerMessage as SatoriMessage
from .models import Role, User, Guild, Login, Channel, Pagination, OuterMember
from .exception import (
    ActionFailed,
    NetworkError,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    ServerErrorException,
    UnauthorizedException,
    MethodNotAllowedException
)

if TYPE_CHECKING:
    from .adapter import Adapter

def _check_reply(
    bot: 'Bot',
    event: MessageEvent
) -> None:
    '''检查消息中存在的回复，赋值 `event.reply`，`event.to_me`'''
    message = event.get_message()
    try:
        index = message.index('quote')
    except ValueError:
        return
    
    msg_seg = message[index]
    event.reply = msg_seg # type: ignore
    
    author_msg = msg_seg.data['content'].get('author')
    if author_msg:
        author_seg = author_msg[0]
        event.to_me = author_seg.data.get('id') == bot.self_id
    
    del message[index]
    if (
        len(message) > index
        and message[index].type == 'at'
        and message[index].data.get('id') == str(bot.self_info.id)
    ):
        del message[index]
    if len(message) > index and message[index].type == 'text':
        message[index].data['text'] = message[index].data['text'].lstrip()
        if not message[index].data['text']:
            del message[index]
    if not message:
        message.append(MessageSegment.text(''))

def _check_at_me(
    bot: 'Bot',
    event: MessageEvent
) -> None:
    def _is_at_me_seg(segment: MessageSegment) -> bool:
        return segment.type == 'at' and segment.data.get('id') == str(bot.self_info.id)
    
    message = event.get_message()
    
    if not message:
        message.append(MessageSegment.text(''))
    
    deleted = False
    if _is_at_me_seg(message[0]):
        message.pop(0)
        event.to_me = True
        deleted = True
        if message and message[0].type == 'text':
            message[0].data['text'] = message[0].data['text'].lstrip('\xa0').lstrip()
            if not message[0].data['text']:
                del message[0]
    
    if not deleted:
        i = -1
        last_msg_seg = message[i]
        if last_msg_seg.type == 'text' and not last_msg_seg.data['text'].strip() and len(message) >= 2:
            i = -1
            last_msg_seg = message[i]
        
        if _is_at_me_seg(last_msg_seg):
            event.to_me = True
            del message[i:]
    
    if not message:
        message.append(MessageSegment.text(''))

class Bot(BaseBot):
    adapter: 'Adapter'
    
    @override
    def __init__(self, adapter: 'Adapter', self_id: str, platform: str, info: ClientInfo) -> None:
        super().__init__(adapter, self_id)
        
        self.info: ClientInfo = info
        self.platform: str = platform
        self._self_info: Optional[User] = None
    
    def __getattr__(self, item: str) -> Any:
        raise AttributeError(f'Object has no attribute "{item}"')
    
    @property
    def ready(self) -> bool:
        '''是否已连接'''
        return self._self_info is not None
    
    @property
    def self_info(self) -> User:
        '''Bot 自身信息'''
        if self._self_info is None:
            raise RuntimeError(f'Bot {self.self_id} of {self.platform} is not connected')
        return self._self_info
    
    def on_ready(self, user: User) -> None:
        self._self_info = user
    
    def get_authorization_header(self) -> dict[str, str]:
        '''获取 Bot 鉴权信息'''
        header = {
            'Authorization': f'Bearer {self.info.token}',
            'X-Self-ID': self.self_id,
            'X-Platform': self.platform
        }
        if not self.info.token:
            del header['Authorization']
        return header
    
    def handle_event(self, event: Event) -> None:
        if isinstance(event, MessageEvent):
            _check_reply(self, event)
            _check_at_me(self, event)
        handle_event(self, event)
    
    def _handle_response(self, response: Response) -> Any:
        if 200 <= response.status_code < 300:
            return response.content and json.loads(response.content)
        elif response.status_code == 400:
            raise BadRequestException(response)
        elif response.status_code == 401:
            raise UnauthorizedException(response)
        elif response.status_code == 403:
            raise ForbiddenException(response)
        elif response.status_code == 404:
            raise NotFoundException(response)
        elif response.status_code == 405:
            raise MethodNotAllowedException(response)
        elif 500 <= response.status_code < 600:
            raise ServerErrorException(response)
        else:
            raise ActionFailed(response)
    
    def _request(self, request: Request) -> Any:
        request.headers.update(self.get_authorization_header())
        
        try:
            response = self.adapter.request(request)
        except Exception as e:
            raise NetworkError('API request failed') from e
        
        return self._handle_response(response)
    
    @override
    def send(
        self,
        event: 'Event',
        message: Union[str, 'Message', 'MessageSegment'],
        **kwargs: Any
    ) -> list[SatoriMessage]:
        if not event.channel:
            raise RuntimeError('Event cannot be replied to')
        return self.message_create(channel_id=event.channel.id, content=str(message))
    
    @override
    def channel_get(self, *, channel_id: str) -> Channel:
        request = Request(
            'POST',
            self.info.api_base / 'channel.get',
            json={'channel_id': channel_id}
        )
        result = self._request(request)
        return Channel.model_validate(result)
    
    @override
    def channel_list(self, *, guild_id: str, next: Optional[str] = None) -> Pagination[Channel]:
        request = Request(
            'POST',
            self.info.api_base / 'channel.list',
            json={'guild_id': guild_id, 'next': next}
        )
        result = self._request(request)
        return Pagination[Channel].model_validate(result)
    
    @override
    def channel_create(self, *, guild_id: str, data: Channel) -> Channel:
        request = Request(
            'POST',
            self.info.api_base / 'channel.create',
            json={'guild_id': guild_id, 'data': data.model_dump()}
        )
        result = self._request(request)
        return Channel.model_validate(result)
    
    @override
    def channel_update(self, *, channel_id: str, data: Channel) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'channel.update',
            json={'channel_id': channel_id, 'data': data.model_dump()}
        )
        self._request(request)
    
    @override
    def channel_delete(self, *, channel_id: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'channel.delete',
            json={'channel_id': channel_id}
        )
        self._request(request)
    
    @override
    def user_channel_create(self, *, user_id: str, guild_id: Optional[str] = None) -> Channel:
        request = Request(
            'POST',
            self.info.api_base / 'user.channel.create',
            json={'user_id': user_id, 'guild_id': guild_id}
        )
        result = self._request(request)
        return Channel.model_validate(result)
    
    @override
    def guild_get(self, *, guild_id: str) -> Guild:
        request = Request(
            'POST',
            self.info.api_base / 'guild.get',
            json={'guild_id': guild_id}
        )
        result = self._request(request)
        return Guild.model_validate(result)
    
    @override
    def guild_list(self, *, next: Optional[str] = None) -> Pagination[Guild]:
        request = Request(
            'POST',
            self.info.api_base / 'guild.list',
            json={'next': next}
        )
        result = self._request(request)
        return Pagination[Guild].model_validate(result)
    
    @override
    def guild_approve(self, *, message_id: str, approve: bool, comment: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.approve',
            json={'message_id': message_id, 'aprove': approve, 'comment': comment}
        )
        self._request(request)
    
    @override
    def guild_member_get(self, *, guild_id: str, user_id: str) -> OuterMember:
        request = Request(
            'POST',
            self.info.api_base / 'guild.member.get',
            json={'guild_id': guild_id, 'user_id': user_id}
        )
        result = self._request(request)
        return OuterMember.model_validate(result)
    
    @override
    def guild_member_list(self, *, guild_id: str, next: Optional[str] = None) -> Pagination[OuterMember]:
        request = Request(
            'POST',
            self.info.api_base / 'guild.member.list',
            json={'guild_id': guild_id, 'next': next}
        )
        result = self._request(request)
        return Pagination[OuterMember].model_validate(result)
    
    @override
    def guild_member_kick(self, *, guild_id: str, user_id: str, permanent: bool) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.member.kick',
            json={'guild_id': guild_id, 'user_id': user_id, 'permanent': permanent}
        )
        self._request(request)
    
    @override
    def guild_member_approve(self, *, message_id: str, approve: bool, comment: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.member.kick',
            json={'message_id': message_id, 'approve': approve, 'comment': comment}
        )
        self._request(request)
    
    @override
    def guild_member_role_set(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.member.role.set',
            json={'guild_id': guild_id, 'user_id': user_id, 'role_id': role_id}
        )
        self._request(request)
    
    @override
    def guild_member_role_unset(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.member.role.unset',
            json={'guild_id': guild_id, 'user_id': user_id, 'role_id': role_id}
        )
        self._request(request)
    
    @override
    def guild_role_list(self, *, guild_id: str, next: Optional[str] = None) -> Pagination[Role]:
        request = Request(
            'POST',
            self.info.api_base / 'guild.role.list',
            json={'guild_id': guild_id, 'next': next}
        )
        result = self._request(request)
        return Pagination[Role].model_validate(result)
    
    @override
    def guild_role_create(self, *, guild_id: str, role: Role) -> Role:
        request = Request(
            'POST',
            self.info.api_base / 'guild.role.create',
            json={'guild_id': guild_id, 'role': role.model_dump()}
        )
        result = self._request(request)
        return Role.model_validate(result)
    
    @override
    def guild_role_update(self, *, guild_id: str, role_id: str, role: Role) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.role.update',
            json={'guild_id': guild_id, 'role_id': role_id, 'role': role.model_dump()}
        )
        self._request(request)
    
    @override
    def guild_role_delete(self, *, guild_id: str, role_id: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'guild.role.delete',
            json={'guild_id': guild_id, 'role_id': role_id}
        )
        self._request(request)
    
    @override
    def login_get(self) -> Login:
        request = Request(
            'POST',
            self.info.api_base / 'login.get'
        )
        result = self._request(request)
        return Login.model_validate(result)
    
    @override
    def message_create(self, *, channel_id: str, content: str) -> list[SatoriMessage]:
        request = Request(
            'POST',
            self.info.api_base / 'message.create',
            json={'channel_id': channel_id, 'content': content}
        )
        result = self._request(request)
        return [SatoriMessage.model_validate(r) for r in list(result)]
    
    @override
    def message_get(self, *, channel_id: str, message_id: str) -> SatoriMessage:
        request = Request(
            'POST',
            self.info.api_base / 'message.get',
            json={'channel_id': channel_id, 'message_id': message_id}
        )
        result = self._request(request)
        return SatoriMessage.model_validate(result)
    
    @override
    def message_delete(self, *, channel_id: str, message_id: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'message.delete',
            json={'channel_id': channel_id, 'message_id': message_id}
        )
        self._request(request)
    
    @override
    def message_update(self, *, channel_id: str, message_id: str, content: str) -> SatoriMessage:
        request = Request(
            'POST',
            self.info.api_base / 'message.update',
            json={'channel_id': channel_id, 'message_id': message_id, 'content': content}
        )
        result = self._request(request)
        return SatoriMessage.model_validate(result)
    
    @override
    def message_list(self, *, channel_id: str, next: Optional[str] = None) -> Pagination[SatoriMessage]:
        request = Request(
            'POST',
            self.info.api_base / 'message.list',
            json={'channel_id': channel_id, 'next': next}
        )
        result = self._request(request)
        return Pagination[SatoriMessage].model_validate(result)
    
    @override
    def reaction_create(self, *, channel_id: str, message_id: str, emoji: str) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'reaction.create',
            json={'channel_id': channel_id, 'message_id': message_id, 'emoji': emoji}
        )
        self._request(request)
    
    @override
    def reaction_delete(self, *, channel_id: str, message_id: str, emoji: str, user_id: Optional[str] = None) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'reaction.delete',
            json={'channel_id': channel_id, 'message_id': message_id, 'emoji': emoji, 'user_id': user_id}
        )
        self._request(request)
    
    @override
    def reaction_clear(self, *, channel_id: str, message_id: str, emoji: Optional[str] = None) -> None:
        request = Request(
            'POST',
            self.info.api_base / 'reaction.clear',
            json={'channel_id': channel_id, 'message_id': message_id, 'emoji': emoji}
        )
        self._request(request)
    
    @override
    def reaction_list(self, *, channel_id: str, message_id: str, emoji: str, next: Optional[str] = None) -> Pagination[User]:
        request = Request(
            'POST',
            self.info.api_base / 'reaction.list',
            json={'channel_id': channel_id, 'message_id': message_id, 'emoji': emoji, 'next': next}
        )
        result = self._request(request)
        return Pagination[User].model_validate(result)
