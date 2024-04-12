'''`anonbot.processor.Processor.permission` 的类型定义'''

from anonbot.params import EventType
from anonbot.adapter import Bot, Event
from anonbot.adapter import EventType as _EventType
from anonbot.internal.permission import USER as USER
from anonbot.internal.permission import User as User
from anonbot.internal.permission import Guild as Guild
from anonbot.internal.permission import Channel as Channel
from anonbot.internal.permission import Permission as Permission

class _Guild:
    '''检查是否为 `Guild` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'Guild()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.GUILD_ADDED,
            _EventType.GUILD_UPDATED,
            _EventType.GUILD_REMOVED,
            _EventType.GUILD_REQUEST
        )

class _GuildMember:
    '''检查是否为 `GuildMember` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'GuildMember()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.GUILD_MEMBER_ADDED,
            _EventType.GUILD_MEMBER_UPDATED,
            _EventType.GUILD_MEMBER_REMOVED,
            _EventType.GUILD_MEMBER_REQUEST
        )

class _GuildRole:
    '''检查是否为 `GuildRole` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'GuildRole()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.GUILD_ROLE_CREATED,
            _EventType.GUILD_ROLE_UPDATED,
            _EventType.GUILD_ROLE_DELETED
        )

class _Interaction:
    '''检查是否为 `Interaction` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'Interaction()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.INTERACTION_BUTTON,
            _EventType.INTERACTION_COMMAND
        )

class _Login:
    '''检查是否为 `Login` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'Login()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.LOGIN_ADDED,
            _EventType.LOGIN_REMOVED,
            _EventType.LOGIN_UPDATED
        )

class _Message:
    '''检查是否为 `Message` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'Message()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.MESSAGE_CREATED,
            _EventType.MESSAGE_UPDATED,
            _EventType.MESSAGE_DELETED
        )

class _Reaction:
    '''检查是否为 `Reaction` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'Reaction()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type in (
            _EventType.REACTION_ADDED,
            _EventType.REACTION_REMOVED
        )

class _User:
    '''检查是否为 `User` 事件'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'User()'
    
    def __call__(self, type: str = EventType()) -> bool:
        return type == _EventType.FRIEND_REQUEST

GUILD_EVENT: Permission = Permission(_Guild())
'''匹配任意 `Guild` 事件'''

GUILD_MEMBER_EVENT: Permission = Permission(_GuildMember())
'''匹配任意 `GuildMember` 事件'''

GUILD_ROLE: Permission = Permission(_GuildRole())
'''匹配任意 `GuildRole` 事件'''

INTERACTION_EVENT: Permission = Permission(_Interaction())
'''匹配任意 `Interaction` 事件'''

LOGIN_EVENT: Permission = Permission(_Login())
'''匹配任意 `Login` 事件'''

MESSAGE_EVENT: Permission = Permission(_Message())
'''匹配任意 `Message` 事件'''

REACTION_EVENT: Permission = Permission(_Reaction())
'''匹配任意 `Reaction` 事件'''

USER_EVENT: Permission = Permission(_User())
'''匹配任意 `User` 事件'''

class SuperUser:
    '''检查是否为超级用户'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'SuperUser()'
    
    def __call__(self, bot: Bot, event: Event) -> bool:
        try:
            user_id = event.get_user_id()
        except Exception:
            return False
        return (
            f'{bot.adapter.get_name().split(maxsplit=1)[0].lower()}:{user_id}'
            in bot.config.superusers
            or user_id in bot.config.superusers
        )

SUPERUSER: Permission = Permission(SuperUser())
'''匹配超级用户'''

__autodoc__ = {
    "Permission": True,
    "Permission.__call__": True,
    "User": True,
    "USER": True,
}
