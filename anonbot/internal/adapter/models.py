from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Any, Generic, TypeVar, Optional

from pydantic import BaseModel

T = TypeVar('T')
C = TypeVar('C', bound='Channel')

class Argv(BaseModel):
    '''交互指令'''
    
    name: str
    '''指令名称'''
    arguments: list[Any]
    '''参数'''
    options: Any
    '''选项'''

class Button(BaseModel):
    '''交互按钮'''
    
    id: str
    '''按钮 ID'''

class ChannelType(IntEnum):
    '''频道类型'''
    
    TEXT = 0
    '''文本频道'''
    DIRECT = 1
    '''私聊频道'''
    CATEGORY = 2
    '''分类频道'''
    VOICE = 3
    '''语音频道'''

class Channel(BaseModel):
    '''频道'''
    
    id: str
    '''频道 ID'''
    type: ChannelType
    '''频道类型'''
    name: Optional[str] = None
    '''频道名称'''
    parent_id: Optional[str] = None
    '''父频道 ID'''

class Guild(BaseModel):
    '''群组'''
    
    id: str
    '''群组 ID'''
    name: Optional[str] = None
    '''群组名称'''
    avatar: Optional[str] = None
    '''群组头像'''

class GuildMember(BaseModel):
    '''群组成员'''
    
    user: Optional['User'] = None
    '''用户对象'''
    nick: Optional[str] = None
    '''用户在群组中的名称'''
    avatar: Optional[str] = None
    '''用户在群组中的头像'''
    joined_at: Optional[datetime] = None
    '''加入时间'''

class GuildRole(BaseModel):
    '''群组角色'''
    
    id: str
    '''角色 ID'''
    name: Optional[str] = None
    '''角色名称'''

class LoginStatus(IntEnum):
    '''登录状态'''
    
    OFFLINE = 0
    '''离线'''
    ONLINE = 1
    '''在线'''
    CONNECT = 2
    '''连接中'''
    DISCONNECT = 3
    '''断开连接'''
    RECONNECT = 4
    '''重新连接'''

class Login(BaseModel):
    '''登录信息'''
    
    user: Optional['User'] = None
    '''用户对象'''
    self_id: Optional[str] = None
    '''平台账号'''
    platform: Optional[str] = None
    '''平台名称'''
    status: LoginStatus = LoginStatus.OFFLINE
    '''登录状态'''

class Message(BaseModel):
    '''消息'''
    
    id: str
    '''消息 ID'''
    content: str
    '''消息内容'''
    channel: Optional[Channel] = None
    '''频道对象'''
    guild: Optional[Guild] = None
    '''群组对象'''
    member: Optional[GuildMember] = None
    '''成员对象'''
    created_at: Optional[datetime] = None
    '''消息发送的时间戳'''
    updated_at: Optional[datetime] = None
    '''消息修改的时间戳'''

class User(BaseModel):
    '''用户'''
    
    id: str
    '''用户 ID'''
    name: Optional[str] = None
    '''用户名称'''
    nick: Optional[str] = None
    '''用户昵称'''
    avatar: Optional[str] = None
    '''用户头像'''
    is_bot: Optional[bool] = None
    '''是否为机器人'''

class Pagination(BaseModel, Generic[T]):
    '''分页列表'''
    
    data: list[T]
    '''数据'''
    next: Optional[str] = None
    '''下一页的令牌'''

class EventType(StrEnum):
    '''事件类型'''
    
    GUILD_ADDED = 'guild-added'
    '''加入群组时触发。必需资源： `guild` 。'''
    GUILD_UPDATED = 'guild-updated'
    '''群组被修改时触发。必需资源： `guild` 。'''
    GUILD_REMOVED = 'guild-removed'
    '''退出群组时触发。必需资源： `guild` 。'''
    GUILD_REQUEST = 'guild-request'
    '''接收到新的入群邀请时触发。必需资源： `guild` 。'''
    
    GUILD_MEMBER_ADDED = 'guild-member-added'
    '''群组成员增加时触发。必需资源： `guild` ， `member` ， `user` 。'''
    GUILD_MEMBER_UPDATED = 'guild-member-updated'
    '''群组成员信息更新时触发。必需资源： `guild` ， `member` ， `user` 。'''
    GUILD_MEMBER_REMOVED = 'guild-member-removed'
    '''群组成员移除时触发。必需资源： `guild` ， `member` ， `user` 。'''
    GUILD_MEMBER_REQUEST = 'guild-member-request'
    '''接收到新的加群请求时触发。必需资源： `guild` ， `member` ， `user` 。'''
    
    GUILD_ROLE_CREATED = 'guild-role-created'
    '''群组角色被创建时触发。必需资源： `guild` ， `role` 。'''
    GUILD_ROLE_UPDATED = 'guild-role-updated'
    '''群组角色被修改时触发。必需资源： `guild` ， `role` 。'''
    GUILD_ROLE_DELETED = 'guild-role-deleted'
    '''群组角色被删除时触发。必需资源： `guild` ， `role` 。'''
    
    INTERACTION_BUTTON = 'interaction/button'
    '''类型为 `action` 的按钮被点击时触发。必需资源： `button` 。'''
    INTERACTION_COMMAND = 'interaction/command'
    '''调用斜线指令时触发。资源 `argv` 或 `message` 中至少包含其一。'''
    
    LOGIN_ADDED = 'login-added'
    '''登录被创建时触发。必需资源： `login` 。'''
    LOGIN_REMOVED = 'login-removed'
    '''登录被删除时触发。必需资源： `login` 。'''
    LOGIN_UPDATED = 'login-updated'
    '''登录信息更新时触发。必需资源： `login` 。'''
    
    MESSAGE_CREATED = 'message-created'
    '''当消息被创建时触发。必需资源： `channel` ， `message` ， `user` 。'''
    MESSAGE_UPDATED = 'message-updated'
    '''当消息被编辑时触发。必需资源： `channel` ， `message` ， `user` 。'''
    MESSAGE_DELETED = 'message-deleted'
    '''当消息被删除时触发。必需资源： `channel` ， `message` ， `user` 。'''
    
    REACTION_ADDED = 'reaction-added'
    '''当表态被添加时触发。'''
    REACTION_REMOVED = 'reaction-removed'
    '''当表态被添加时触发。'''
    
    FRIEND_REQUEST = 'friend-request'
    '''接收到新的好友申请时触发。必需资源： `user` 。'''
    
    INTERNAL = 'internal'
    '''内部事件'''
