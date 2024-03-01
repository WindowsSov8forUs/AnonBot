'''AnonBot 的一些共享类型'''

from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeVar,
    Callable,
    ParamSpec,
    TypeAlias
)

if TYPE_CHECKING:
    from anonbot.adapter import Bot
    from anonbot.permission import Permission

T = TypeVar('T')
P = ParamSpec('P')

StateType: TypeAlias = dict[Any, Any]
'''事件处理状态'''

CommandStart: TypeAlias = Literal['/', '!', '！', '']
'''命令前缀'''

_DependentCallable: TypeAlias = Callable[..., T]

RuleChecker: TypeAlias = _DependentCallable[bool]
'''判断是否响应事件'''

PermissionChecker: TypeAlias = _DependentCallable[bool]
'''判断事件是否满足权限'''

HandlerType: TypeAlias = _DependentCallable[Any]
'''处理函数'''

TypeUpdater: TypeAlias = _DependentCallable[Any]
'''用于更新响应的事件类型'''

PermissionUpdater: TypeAlias = _DependentCallable['Permission']
'''用于更新会话对象权限'''

DependencyCache: TypeAlias = dict[_DependentCallable[Any], Any]
'''依赖缓存'''
