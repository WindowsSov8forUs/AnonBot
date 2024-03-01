'''AnonBot 协议适配器基类'''

from anonbot.internal.adapter import Bot as Bot
from anonbot.internal.adapter import Event as Event
from anonbot.internal.adapter import Adapter as Adapter
from anonbot.internal.adapter import Message as Message
from anonbot.internal.adapter import MessageSegment as MessageSegment

from anonbot.internal.adapter import (
    Argv as Argv,
    User as User,
    Guild as Guild,
    Login as Login,
    Button as Button,
    Channel as Channel,
    EventType as EventType,
    GuildRole as GuildRole,
    Pagination as Pagination,
    GuildMember as GuildMember,
    ChannelType as ChannelType,
    LoginStatus as LoginStatus,
    MessageModel as MessageModel
)

__autodoc__ = {
    'Bot': True,
    'Event': True,
    'Adapter': True,
    'Message': True,
    'Message.__getitem__': True,
    'Message.__contains__': True,
    'Message._construct': True,
    'MessageSegment': True,
    'MessageSegment.__str__': True,
    'MessageSegment.__add__': True
}