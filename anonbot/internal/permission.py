from contextlib import ExitStack
from typing import Self, Tuple, Union, NoReturn, Optional

from anonbot.utils import run_with_catch
from anonbot.dependency import Dependent
from anonbot.threading import Task, gather
from anonbot.exception import SkippedException
from anonbot.typing import DependencyCache, PermissionChecker

from .adapter import Bot, Event
from .params import BotParam, EventParam, DependParam, DefaultParam

class Permission:
    '''`anonbot.processor.Processor` 权限类'''
    
    __slots__ = ('checkers')
    
    HANDLER_PARAM_TYPES = [
        DependParam,
        BotParam,
        EventParam,
        DefaultParam
    ]
    
    def __init__(self, *checkers: Union[PermissionChecker, Dependent[bool]]) -> None:
        self.checkers: set[Dependent[bool]] = {
            checker if isinstance(checker, Dependent)
            else Dependent[bool].parse(
                call=checker, allow_types=self.HANDLER_PARAM_TYPES
            ) for checker in checkers
        }
    
    def __repr__(self) -> str:
        return f'Permission({", ".join(repr(checker) for checker in self.checkers)})'
    
    def __call__(
        self,
        bot: Bot,
        event: Event,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> bool:
        '''检查是否满足权限'''
        if not self.checkers:
            return True
        tasks: list[Task] = [
            Task(
                checker,
                bot=bot,
                event=event,
                stack=stack,
                dependency_cache=dependency_cache
            ) for checker in self.checkers
        ]
        result = gather(
            *(Task(run_with_catch, task, SkippedException, False) for task in tasks)
        )
        return any(result)
    
    def __and__(self, other: object) -> NoReturn:
        raise RuntimeError("And operation between Permissions is not allowed.")

    def __or__(
        self, other: Optional[Union["Permission", PermissionChecker]]
    ) -> "Permission":
        if other is None:
            return self
        elif isinstance(other, Permission):
            return Permission(*self.checkers, *other.checkers)
        else:
            return Permission(*self.checkers, other)
    
    def __ror__(
        self, other: Optional[Union["Permission", PermissionChecker]]
    ) -> "Permission":
        if other is None:
            return self
        elif isinstance(other, Permission):
            return Permission(*other.checkers, *self.checkers)
        else:
            return Permission(other, *self.checkers)

class User:
    '''检查当前事件是否属于指定对话

    参数:
        users (Tuple[str, ...]): 会话 ID 元组
        perm (Optional[Permission], optional): 需同时满足的权限
    '''
    
    __slots__ = ('users', 'perm')
    
    def __init__(self, users: Tuple[str, ...], perm: Optional[Permission] = None) -> None:      
        self.users = users
        self.perm = perm
    
    def __repr__(self) -> str:
        return (
            f'User(users={self.users}'
            + (f', permission={self.perm}' if self.perm else '')
            + ')'
        )
    
    def __call__(self, bot: Bot, event: Event) -> bool:
        try:
            session = event.get_session_id()
        except Exception:
            return False
        return bool(
            session in self.users and (self.perm is None or self.perm(bot, event))
        )
    
    @classmethod
    def _clean_permission(cls, perm: Permission) -> Optional[Permission]:
        if len(perm.checkers) == 1 and isinstance(
            user_perm := tuple(perm.checkers)[0].call, cls
        ):
            return user_perm.perm
        return perm
    
    @classmethod
    def from_event(cls, event: Event, perm: Optional[Permission] = None) -> Self:
        '''从事件中获取会话 ID'''
        return cls((event.get_session_id(),), perm=perm and cls._clean_permission(perm))
    
    @classmethod
    def from_permission(cls, *users: str, perm: Optional[Permission] = None) -> Self:
        '''指定会话与权限'''
        return cls(users, perm=perm and cls._clean_permission(perm))

class Channel:
    '''检查当前事件是否属于指定频道

    参数:
        channels (Tuple[str, ...]): 频道 ID 元组
        perm (Optional[Permission], optional): 需同时满足的权限
    '''
    
    __slots__ = ('channels', 'perm')
    
    def __init__(self, channels: Tuple[str, ...], perm: Optional[Permission] = None) -> None:
        self.channels = channels
        self.perm = perm
    
    def __repr__(self) -> str:
        return (
            f'Channel(channels={self.channels}'
            + (f', permission={self.perm}' if self.perm else '')
            + ')'
        )
    
    def __call__(self, bot: Bot, event: Event) -> bool:
        try:
            channel = event.get_channel()
            if channel is None:
                return False
        except Exception:
            return False
        return bool(
            channel.id in self.channels and (self.perm is None or self.perm(bot, event))
        )
    
    @classmethod
    def _clean_permission(cls, perm: Permission) -> Optional[Permission]:
        if len(perm.checkers) == 1 and isinstance(
            channel_perm := tuple(perm.checkers)[0].call, cls
        ):
            return channel_perm.perm
        return perm
    
    @classmethod
    def from_event(cls, event: Event, perm: Optional[Permission] = None) -> Self:
        '''从事件中获取频道 ID'''
        if (channel := event.get_channel()) is not None:
            return cls((channel.id,), perm=perm and cls._clean_permission(perm))
        raise TypeError(f'Event {event} has no channel')
    
    @classmethod
    def from_permission(cls, *channels: str, perm: Optional[Permission] = None) -> Self:
        '''指定频道与权限'''
        return cls(channels, perm=perm and cls._clean_permission(perm))

class Guild:
    '''检查当前事件是否属于指定群组

    参数:
        guilds (Tuple[str, ...]): 群组 ID 元组
        perm (Optional[Permission], optional): 需同时满足的权限
    '''
    
    __slots__ = ('guilds', 'perm')
    
    def __init__(self, guilds: Tuple[str, ...], perm: Optional[Permission] = None) -> None:
        self.guilds = guilds
        self.perm = perm
    
    def __repr__(self) -> str:
        return (
            f'Guild(guilds={self.guilds}'
            + (f', permission={self.perm}' if self.perm else '')
            + ')'
        )
    
    def __call__(self, bot: Bot, event: Event) -> bool:
        try:
            guild = event.get_guild()
            if guild is None:
                return False
        except Exception:
            return False
        return bool(
            guild.id in self.guilds and (self.perm is None or self.perm(bot, event))
        )
    
    @classmethod
    def _clean_permission(cls, perm: Permission) -> Optional[Permission]:
        if len(perm.checkers) == 1 and isinstance(
            guild_perm := tuple(perm.checkers)[0].call, cls
        ):
            return guild_perm.perm
        return perm
    
    @classmethod
    def from_event(cls, event: Event, perm: Optional[Permission] = None) -> Self:
        '''从事件中获取群组 ID'''
        if (guild := event.get_guild()) is not None:
            return cls((guild.id,), perm=perm and cls._clean_permission(perm))
        raise TypeError(f'Event {event} has no guild')
    
    @classmethod
    def from_permission(cls, *guilds: str, perm: Optional[Permission] = None) -> Self:
        '''指定群组与权限'''
        return cls(guilds, perm=perm and cls._clean_permission(perm))

def USER(*users: str, perm: Optional[Permission] = None) -> Permission:
    '''匹配当前事件属于指定会话

    参数:
        users (str): 会话白名单
        perm (Optional[Permission], optional): 需同时满足的权限
    '''
    
    return Permission(User.from_permission(*users, perm=perm))
