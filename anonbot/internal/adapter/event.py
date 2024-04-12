import abc
from datetime import datetime
from typing import Any, Type, Union, TypeVar, Optional

from pydantic import BaseModel, ConfigDict, TypeAdapter

from .message import Message
from .models import Message as SatoriMessage
from .uni.message import Message as UniMessage
from .models import (
    Argv,
    User,
    Guild,
    Login,
    Button,
    Channel,
    EventType,
    GuildRole,
    GuildMember
)

E = TypeVar('E', bound='Event')

class Event(abc.ABC, BaseModel):
    '''Event 基类'''
    
    model_config = ConfigDict(extra='allow')
    
    @abc.abstractmethod
    def get_id(self) -> int:
        '''事件 ID'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_event_type(self) -> EventType:
        '''事件类型'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_platform(self) -> str:
        '''接收者的平台名称'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_self_id(self) -> str:
        '''接收者的平台账号'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_timestamp(self) -> datetime:
        '''事件的时间戳'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_argv(self) -> Optional[Argv]:
        '''交互指令'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_button(self) -> Optional[Button]:
        '''交互按钮'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_channel(self) -> Optional[Channel]:
        '''事件所属的频道'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_guild(self) -> Optional[Guild]:
        '''事件所属的群组'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_login(self) -> Optional[Login]:
        '''事件的登录信息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_member(self) -> Optional[GuildMember]:
        '''事件的目标成员'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_message_data(self) -> Optional[SatoriMessage]:
        '''事件的消息'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_operator(self) -> Optional[User]:
        '''事件的操作者'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_role(self) -> Optional[GuildRole]:
        '''事件的目标角色'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_user(self) -> Optional[User]:
        '''事件的目标用户'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_origin_type(self) -> Optional[str]:
        '''平台通用名称'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_origin_data(self) -> Optional[dict[str, Any]]:
        '''原生事件数据'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_uni_message(self) -> UniMessage:
        '''事件的通用消息'''
        raise NotImplementedError
    
    @classmethod
    def validate(cls: Type['E'], value: Any) -> 'E':
        if isinstance(value, Event) and not isinstance(value, cls):
            raise TypeError(f'{value} is incompatible with Event type {cls}')
        return TypeAdapter(cls).validate_python(value)
    
    @abc.abstractmethod
    def get_type(self) -> Union[EventType, str]:
        '''获取事件类型，通常为 Satori 协议事件类型'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_event_name(self) -> str:
        '''获取事件名称'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_event_description(self) -> str:
        '''获取事件描述'''
        raise NotImplementedError
    
    def __str___(self) -> str:
        return f'[{self.get_event_name()}]: {self.get_event_description()}'
    
    def get_log_string(self) -> str:
        '''获取事件日志信息'''
        return f'[{self.get_event_name()}]: {self.get_event_description()}'
    
    @abc.abstractmethod
    def get_user_id(self) -> str:
        '''获取事件主体 ID'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_session_id(self) -> str:
        '''获取事件会话 ID'''
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_message(self) -> Message:
        '''获取事件消息'''
        raise NotImplementedError
    
    def get_plaintext(self) -> str:
        '''获取事件消息的纯文本'''
        return self.get_message().extract_plain_text()
    
    @abc.abstractmethod
    def is_tome(self) -> bool:
        '''获取事件是否与机器人有关'''
        raise NotImplementedError