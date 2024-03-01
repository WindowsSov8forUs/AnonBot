from contextlib import ExitStack
from typing import Self, Tuple, Union, NoReturn, Optional

from anonbot.threading import gather
from anonbot.utils import run_with_catch
from anonbot.dependency import Dependent
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
        result = gather(
            *(
                (
                    run_with_catch,
                    (checker, (SkippedException,), False),
                    {
                        'bot': bot,
                        'event': event,
                        'stack': stack,
                        'dependency_cache': dependency_cache
                    }
                ) for checker in self.checkers
            )
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

def USER(*users: str, perm: Optional[Permission] = None) -> Permission:
    '''匹配当前事件属于指定会话

    参数:
        users (str): 会话白名单
        perm (Optional[Permission], optional): 需同时满足的权限
    '''
    
    return Permission(User.from_permission(*users, perm=perm))
