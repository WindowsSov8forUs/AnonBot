'''事件处理主要流程'''

import contextlib
from datetime import datetime
from contextlib import ExitStack
from typing import TYPE_CHECKING, Any, Type, Optional

from anonbot.log import logger
from anonbot.rule import TrieRule
from anonbot.threading import gather
from anonbot.processor import Processor, processors
from anonbot.typing import StateType, DependencyCache
from anonbot.exception import (
    NoLogException,
    StopPropagation
)
from anonbot.internal.params import (
    BotParam,
    EventParam,
    StateParam,
    DependParam,
    DefaultParam
)

if TYPE_CHECKING:
    from anonbot.adapter import Bot, Event

EVENT_CS_PARAMS = (
    DependParam,
    BotParam,
    EventParam,
    StateParam,
    DefaultParam
)

def _check_processor(
    Processor: Type[Processor],
    bot: 'Bot',
    event: 'Event',
    state: StateType,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None
) -> bool:
    '''检查事件处理器是否符合运行条件'''
    if Processor.expire_time and datetime.now() > Processor.expire_time:
        with contextlib.suppress(Exception):
            Processor.destroy()
        return False
    
    try:
        if not Processor.check_perm(bot, event, stack, dependency_cache):
            logger.trace(f'Permission denied: {Processor}')
            return False
    except Exception as exception:
        logger.error(f'Error occurred while checking permission: {Processor}', exception=exception)
        return False
    
    try:
        if not Processor.check_rule(bot, event, state, stack, dependency_cache):
            logger.trace(f'Rule denied: {Processor}')
            return False
    except Exception as exception:
        logger.error(f'Error occurred while checking rule: {Processor}', exception=exception)
        return False
    
    return True

def _run_processor(
    Processor: Type[Processor],
    bot: 'Bot',
    event: 'Event',
    state: StateType,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None
) -> None:
    '''运行事件处理器'''
    logger.debug(f'Processor in run: {Processor}')
    
    if Processor.temp:
        with contextlib.suppress(Exception):
            Processor.destroy()
    
    processor = Processor()

    try:
        logger.debug(f'Running processor: {Processor}')
        processor.run(bot, event, state, stack, dependency_cache)
    except Exception as e:
        logger.error(f'Error occurred while running processor: {Processor}', exception=e)
    
    if processor.block:
        raise StopPropagation

def check_and_run_processor(
    Processor: Type[Processor],
    bot: 'Bot',
    event: 'Event',
    state: StateType,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None
) -> None:
    '''检查并运行事件处理器

    参数:
        Processor (Type[Processor]): 事件处理器
        bot (Bot): 机器人对象
        event (Event): 事件对象
        state (StateType): 状态对象
        stack (Optional[ExitStack], 可选): 上下文管理器栈
        dependency_cache (Optional[DependencyCache], 可选): 依赖缓存
    '''
    if not _check_processor(Processor, bot, event, state, stack, dependency_cache):
        return
    
    _run_processor(Processor, bot, event, state, stack, dependency_cache)

def handle_event(bot: 'Bot', event: 'Event') -> None:
    '''分发并处理一个事件

    参数:
        bot (Bot): 机器人对象
        event (Event): 事件对象
    '''
    show_log = True
    log_message = ''
    try:
        log_message = event.get_log_string()
    except NoLogException:
        show_log = False
    if show_log:
        logger.info(log_message)
    
    state: dict[Any, Any] = {}
    dependency_cache: DependencyCache = {}
    
    with ExitStack() as stack:
        try:
            TrieRule.get_value(bot, event, state)
        except Exception as e:
            logger.warn('Error occurred while arsing command', exception=e)
    
    break_flag = False
    for priority in sorted(processors.keys()):
        if break_flag:
            break
        
        if show_log:
            logger.debug(f'Running processors with priority {priority}')
        
        pending_tasks = [
            (
                check_and_run_processor,
                (processor, bot, event, state.copy(), stack, dependency_cache)
            ) for processor in processors[priority]
        ]
        results = gather(*pending_tasks, return_exceptions=True)
        for result in results:
            if not isinstance(result, Exception):
                continue
            if isinstance(result, StopPropagation):
                break_flag = True
                logger.debug('Propagation stopped')
            else:
                logger.error('Error occurred while running processor', exception=result)
    
    if show_log:
        logger.debug('Event handling finished')
