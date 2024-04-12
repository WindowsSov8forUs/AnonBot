'''事件处理器便携定义函数'''

import re
import inspect
from types import ModuleType
from datetime import datetime, timedelta
from typing import Any, Type, Tuple, Union, Optional

from anonbot.dependency import Dependent
from anonbot.permission import Permission
from anonbot.adapter import Event, EventType
from anonbot.processor import Processor, ProcessorSource
from anonbot.typing import StateType, HandlerType, CommandStart, RuleChecker, PermissionChecker
from anonbot.rule import (
    Rule,
    regex,
    command,
    is_type,
    keyword,
    endswith,
    fullmatch,
    startswith
)

from .model import Plugin
from . import get_plugin_by_module_name
from .manager import _current_plugin_chain

def store_processor(processor: Type[Processor]) -> None:
    '''存储一个事件处理器到插件

    参数:
        processor (Type[Processor]): 事件处理器
    '''
    if plugin_chain := _current_plugin_chain.get():
        plugin_chain[-1].processors.add(processor)

def get_processor_source(depth: int = 1) -> Optional[ProcessorSource]:
    '''获取事件处理器定义源码信息

    参数:
        depth (int): 调用栈深度
    '''
    current_frame = inspect.currentframe()
    if current_frame is None:
        return None
    frame = inspect.getouterframes(current_frame)[depth + 1].frame
    
    module_name = (module := inspect.getmodule(frame)) and module.__name__
    
    plugin: Optional['Plugin'] = None
    if plugin_chain := _current_plugin_chain.get():
        plugin = plugin_chain[-1]
    elif module_name:
        plugin = get_plugin_by_module_name(module_name)
    
    return ProcessorSource(
        plugin_name=plugin and plugin.name,
        module_name=module_name,
        lineno=frame.f_lineno
    )

def on(
    type: EventType,
    name: str,
    rule: Optional[Union[Rule, RuleChecker]] = None,
    permission: Optional[Union[Permission, PermissionChecker]] = None,
    *,
    handlers: Optional[list[Union[HandlerType, Dependent]]] = None,
    temp: bool = False,
    expire_time: Optional[Union[datetime, timedelta]] = None,
    priority: int = 1,
    block: bool = False,
    state: Optional[StateType] = None,
    _depth: int = 0
) -> Type[Processor]:
    '''注册一个事件处理器，可自定义类型

    参数:
        type (EventType): 事件类型，为 Satori 协议规定事件类型
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    processor = Processor.new(
        name,
        type,
        Rule() & rule,
        Permission() | permission,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        block=block,
        handlers=handlers,
        source=get_processor_source(_depth + 1),
        default_state=state
    )
    store_processor(processor)
    return processor

def on_guild_added(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个加入群组时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_ADDED, *args, **kwargs, _depth=_depth + 1)

def on_guild_updated(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组被修改时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_UPDATED, *args, **kwargs, _depth=_depth + 1)

def on_guild_removed(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个退出群组时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_REMOVED, *args, **kwargs, _depth=_depth + 1)

def on_guild_request(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个接收到新的入群邀请时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_REQUEST, *args, **kwargs, _depth=_depth + 1)

def on_guild_member_added(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组成员增加时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_MEMBER_ADDED, *args, **kwargs, _depth=_depth + 1)

def on_guild_member_updated(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组成员信息更新时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_MEMBER_UPDATED, *args, **kwargs, _depth=_depth + 1)

def on_guild_member_removed(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组成员移除时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_MEMBER_REMOVED, *args, **kwargs, _depth=_depth + 1)

def on_guild_member_request(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个接收到新的加群请求时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_MEMBER_REQUEST, *args, **kwargs, _depth=_depth + 1)

def on_guild_role_created(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组角色被创建时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_ROLE_CREATED, *args, **kwargs, _depth=_depth + 1)

def on_guild_role_updated(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组角色被修改时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_ROLE_UPDATED, *args, **kwargs, _depth=_depth + 1)

def on_guild_role_deleted(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个群组角色被删除时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.GUILD_ROLE_DELETED, *args, **kwargs, _depth=_depth + 1)

def on_interaction_button(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个类型为 `action` 的按钮被点击时事件处理器
    
    此事件仅在支持 Satori 协议按钮的平台上可用

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.INTERACTION_BUTTON, *args, **kwargs, _depth=_depth + 1)

def on_interaction_command(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个调用斜线指令时事件处理器
    
    此事件仅在提供后台斜线指令事件的平台可用

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.INTERACTION_COMMAND, *args, **kwargs, _depth=_depth + 1)

def on_login_added(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个登录被创建时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.LOGIN_ADDED, *args, **kwargs, _depth=_depth + 1)

def on_login_removed(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个登录被删除时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.LOGIN_REMOVED, *args, **kwargs, _depth=_depth + 1)

def on_login_updated(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个登录信息更新时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.LOGIN_UPDATED, *args, **kwargs, _depth=_depth + 1)

def on_message_created(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个消息被创建时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.MESSAGE_CREATED, *args, **kwargs, _depth=_depth + 1)

def on_message_updated(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个消息被编辑时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.MESSAGE_UPDATED, *args, **kwargs, _depth=_depth + 1)

def on_message_deleted(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个消息被删除时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.MESSAGE_DELETED, *args, **kwargs, _depth=_depth + 1)

def on_reaction_added(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个表态被添加时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.REACTION_ADDED, *args, **kwargs, _depth=_depth + 1)

def on_reaction_removed(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个表态被移除时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.REACTION_REMOVED, *args, **kwargs, _depth=_depth + 1)

def on_friend_request(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个接收到新的好友申请时事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.FRIEND_REQUEST, *args, **kwargs, _depth=_depth + 1)

def on_internal(*args, _depth: int = 0, **kwargs) -> Type[Processor]:
    '''注册一个内部事件处理器

    参数:
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on(EventType.INTERNAL, *args, **kwargs, _depth=_depth + 1)

def on_startswith(
    name: str,
    msg: Union[str, Tuple[str, ...]],
    rule: Optional[Union[Rule, RuleChecker]] = None,
    ignorecase: bool = False,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个消息事件处理器，当消息文本部分以指定内容开头时响应

    参数:
        name (str): 处理器名称
        msg (Union[str, Tuple[str, ...]]): 消息文本开头内容
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        ignorecase (bool): 是否忽略大小写
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on_message_created(name, startswith(msg, ignorecase) & rule, **kwargs, _depth=_depth + 1)

def on_endswith(
    name: str,
    msg: Union[str, Tuple[str, ...]],
    rule: Optional[Union[Rule, RuleChecker]] = None,
    ignorecase: bool = False,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个消息事件处理器，当消息文本部分以指定内容结尾时响应

    参数:
        name (str): 处理器名称
        msg (Union[str, Tuple[str, ...]]): 消息文本结尾内容
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        ignorecase (bool): 是否忽略大小写
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on_message_created(name, endswith(msg, ignorecase) & rule, **kwargs, _depth=_depth + 1)

def on_fullmatch(
    name: str,
    msg: Union[str, Tuple[str, ...]],
    rule: Optional[Union[Rule, RuleChecker]] = None,
    ignorecase: bool = False,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个消息事件处理器，当消息文本完全匹配指定内容时响应

    参数:
        name (str): 处理器名称
        msg (Union[str, Tuple[str, ...]]): 消息文本完全匹配内容
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        ignorecase (bool): 是否忽略大小写
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on_message_created(name, fullmatch(msg, ignorecase) & rule, **kwargs, _depth=_depth + 1)

def on_keyword(
    name: str,
    keywords: set[str],
    rule: Optional[Union[Rule, RuleChecker]] = None,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个消息事件处理器，当消息文本包含指定关键词时响应

    参数:
        name (str): 处理器名称
        keywords (set[str]): 关键词集合
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on_message_created(name, keyword(*keywords) & rule, **kwargs, _depth=_depth + 1)

def on_command(
    name: str,
    cmd: str,
    command_start: Union[CommandStart, Tuple[CommandStart, ...]] = '/',
    rule: Optional[Union[Rule, RuleChecker]] = None,
    aliases: Optional[set[str]] = None,
    force_whitespace: Optional[Union[str, bool]] = None,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个消息事件处理器，当消息文本为指定命令开头时响应

    参数:
        name (str): 处理器名称
        cmd (str): 命令名称
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        aliases (Optional[set[str]]): 命令别名集合
        force_whitespace (Optional[Union[str, bool]]): 强制空格分隔参数，若为 `True` 则强制空格分隔，若为 `False` 则不强制空格分隔，若为字符串则强制使用指定字符串分隔
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    commands = {cmd} | (aliases or set())
    kwargs.setdefault('block', False)
    return on_message_created(
        name,
        command(*commands, command_start=command_start, force_whitespace=force_whitespace) & rule,
        **kwargs,
        _depth=_depth + 1
    )

def on_regex(
    name: str,
    pattern: str,
    flags: Union[int, re.RegexFlag] = 0,
    rule: Optional[Union[Rule, RuleChecker]] = None,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个消息事件处理器，当消息文本匹配指定正则表达式时响应

    参数:
        name (str): 处理器名称
        pattern (str): 正则表达式
        flags (Union[int, re.RegexFlag]): 正则表达式标志
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    return on_message_created(name, regex(pattern, flags) & rule, **kwargs, _depth=_depth + 1)

def on_type(
    name: str,
    types: Union[Type[Event], Tuple[Type[Event], ...]],
    rule: Optional[Union[Rule, RuleChecker]] = None,
    *,
    _depth: int = 0,
    **kwargs
) -> Type[Processor]:
    '''注册一个事件处理器，当事件类型为指定类型时响应

    参数:
        name (str): 处理器名称
        types (Union[Type[Event], Tuple[Type[Event], ...]]): 事件类型
        rule (Optional[Union[Rule, RuleChecker]]): 响应规则，同时满足规则的事件才会被处理
        permission (Optional[Union[Permission, PermissionChecker]]): 响应权限，任一权限满足的事件才会被处理
        handlers (Optional[list[Union[HandlerType, Dependent]]]): 处理函数列表（一般无需手动添加）
        temp (bool): 是否为临时处理器（仅执行一次，一般保留默认值）
        expire_time (Optional[Union[datetime, timedelta]]): 处理器有效时间（一般无需手动添加）
        priority (int): 事件处理优先级
        block (bool): 是否阻塞事件（一般无需手动添加）
        state (Optional[StateType]): 默认 state（一般无需手动添加）
    '''
    event_type = types if isinstance(types, tuple) else (types,)
    return on(name=name, rule=is_type(*event_type) & rule, **kwargs, _depth=_depth + 1)
