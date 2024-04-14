import abc
from functools import partial
from typing import TYPE_CHECKING, Any, Type, Union, Optional, Protocol

from anonbot.config import Config

from .models import Message as MessageModel
from .models import (
    User,
    Guild,
    Login,
    Channel,
    GuildRole,
    Pagination,
    GuildMember
)

if TYPE_CHECKING:
    from .event import Event
    from .adapter import Adapter
    from .uni import Message as UniMessage
    from .message import Message, MessageSegment
    
    class _ApiCall(Protocol):
        def __call__(self, **kwargs: Any) -> Any:
            ...

class Bot(abc.ABC):
    '''Bot 基类

    用于处理上报消息，并提供 API 调用接口。

    参数:
        adapter (Adapter): 协议适配器实例
        self_id (str): 机器人 ID
    '''
    def __init__(self, adapter: 'Adapter', self_id: str) -> None:
        self.adapter: 'Adapter' = adapter
        '''协议适配器实例'''
        self.self_id: str = self_id
        '''机器人 ID'''
    
    def __repr__(self) -> str:
        return f'Bot(type={self.type!r}, self_id={self.self_id!r})'
    
    def __getattr__(self, name: str) -> '_ApiCall':
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(f'{self.__class__.__name__} object has no attribute {name}')
        return partial(self.call_api, name)
    
    @property
    def type(self) -> str:
        '''协议适配器名称'''
        return self.adapter.get_name()
    
    @property
    def config(self) -> Config:
        '''当前 AnonBot 配置'''
        return self.adapter.config
    
    def call_api(self, api: str, **data: Any) -> Any:
        '''调用机器人 API 接口

        参数:
            api (str): API 名称
            **data (Any): API 数据
        '''
        try:
            return self.adapter._call_api(self, api, **data)
        except Exception as exception:
            raise exception
    
    @abc.abstractmethod
    def send(
        self,
        event: 'Event',
        message: Union[str, 'Message', 'MessageSegment', 'UniMessage'],
        **kwargs: Any
    ) -> Any:
        '''调用机器人基础发送消息接口

        参数:
            event (Event): 上报事件
            message (str | Message | MessageSegment | UniMessage): 要发送的消息
            **kwargs (Any): 任意额外参数
        '''
        raise NotImplementedError
    
    @abc.abstractmethod
    def channel_get(self, *, channel_id: str) -> Type[Channel]:
        '''获取群组频道'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def channel_list(self, *, guild_id: str, next: Optional[str] = None) -> Pagination[Channel]:
        '''获取群组频道列表'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def channel_create(self, *, guild_id: str, data: Type[Channel]) -> Type[Channel]:
        '''创建群组频道'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def channel_update(self, *, channel_id: str, data: Type[Channel]) -> None:
        '''修改群组频道'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def channel_delete(self, *, channel_id: str) -> None:
        '''删除群组频道'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def user_channel_create(self, *, user_id: str, guild_id: Optional[str] = None) -> Type[Channel]:
        '''创建私聊频道'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_get(self, *, guild_id: str) -> Type[Guild]:
        '''获取群组'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_list(self, *, next: Optional[str] = None) -> Pagination[Guild]:
        '''获取群组列表'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_approve(self, *, message_id: str, approve: bool, comment: str) -> None:
        '''处理群组邀请'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_member_get(self, *, guild_id: str, user_id: str) -> Type[GuildMember]:
        '''获取群组成员'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_member_list(self, *, guild_id: str, next: Optional[str] = None) -> Pagination[GuildMember]:
        '''获取群组成员列表'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_member_kick(self, *, guild_id: str, user_id: str, permanent: bool) -> None:
        '''踢出群组成员'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_member_approve(self, *, message_id: str, approve: bool, comment: str) -> None:
        '''通过群组成员申请'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_member_role_set(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        '''设置群组成员角色'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_member_role_unset(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        '''取消群组成员角色'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_role_list(self, *, guild_id: str, next: Optional[str] = None) -> Pagination[GuildRole]:
        '''获取群组角色列表'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_role_create(self, *, guild_id: str, role: Type[GuildRole]) -> Type[GuildRole]:
        '''创建群组角色'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_role_update(self, *, guild_id: str, role_id: str, role: Type[GuildRole]) -> None:
        '''修改群组角色'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def guild_role_delete(self, *, guild_id: str, role_id: str) -> None:
        '''删除群组角色'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def login_get(self) -> Type[Login]:
        '''获取登录信息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def message_create(self, *, channel_id: str, content: str) -> list[MessageModel]:
        '''发送消息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def message_get(self, *, channel_id: str, message_id: str) -> Type[MessageModel]:
        '''获取消息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def message_delete(self, *, channel_id: str, message_id: str) -> None:
        '''撤回消息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def message_update(self, *, channel_id: str, message_id: str, content: str) -> Type[MessageModel]:
        '''编辑消息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def message_list(self, *, channel_id: str, next: Optional[str] = None) -> Pagination[MessageModel]:
        '''获取消息列表'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def reaction_create(self, *, channel_id: str, message_id: str, emoji: str) -> None:
        '''添加表态'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def reaction_delete(self, *, channel_id: str, message_id: str, emoji: str, user_id: Optional[str] = None) -> None:
        '''删除表态'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def reaction_clear(self, *, channel_id: str, message_id: str, emoji: Optional[str] = None) -> None:
        '''清除表态'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def reaction_list(self, *, channel_id: str, message_id: str, emoji: str, next: Optional[str] = None) -> Pagination[User]:
        '''获取表态列表'''
        raise NotImplementedError
