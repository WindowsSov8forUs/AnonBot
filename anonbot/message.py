'''事件处理主要流程'''

import contextlib
from datetime import datetime
from contextlib import ExitStack
from typing import TYPE_CHECKING, Any, Type, Optional

from anonbot.log import logger
from anonbot.rule import TrieRule
from anonbot.utils import run_with_catch
from anonbot.dependency import Dependent
from anonbot.threading import Task, gather
from anonbot.processor import Processor, processors
from anonbot.typing import (
    StateType,
    DependencyCache,
    RunPreProcessor,
    RunPostProcessor,
    EventPreProcessor,
    EventPostProcessor
)
from anonbot.exception import (
    NoLogException,
    StopPropagation,
    SkippedException,
    IgnoredException
)
from anonbot.internal.params import (
    ArgParam,
    BotParam,
    EventParam,
    StateParam,
    DependParam,
    DefaultParam,
    ExceptionParam,
    ProcessorParam
)

if TYPE_CHECKING:
    from anonbot.adapter import Bot, Event

EVENT_PCS_PARAMS = (
    DependParam,
    BotParam,
    EventParam,
    StateParam,
    DefaultParam
)
RUN_PREPCS_PARAMS = (
    DependParam,
    BotParam,
    EventParam,
    StateParam,
    ArgParam,
    ProcessorParam,
    DefaultParam,
)
RUN_POSTPCS_PARAMS = (
    DependParam,
    ExceptionParam,
    BotParam,
    EventParam,
    StateParam,
    ArgParam,
    ProcessorParam,
    DefaultParam,
)

_event_preprocessors: set[Dependent[Any]] = set()
_event_postprocessors: set[Dependent[Any]] = set()
_run_preprocessors: set[Dependent[Any]] = set()
_run_postprocessors: set[Dependent[Any]] = set()

def event_preprocessor(func: EventPreProcessor) -> EventPreProcessor:
    '''事件预处理

    装饰一个函数，使其在事件被分发给各处理器之前执行
    '''
    _event_preprocessors.add(
        Dependent[Any].parse(call=func, allow_types=EVENT_PCS_PARAMS)
    )
    return func

def event_postprocessor(func: EventPostProcessor) -> EventPostProcessor:
    '''事件后处理

    装饰一个函数，使其在事件被分发给各处理器之后执行
    '''
    _event_postprocessors.add(
        Dependent[Any].parse(call=func, allow_types=EVENT_PCS_PARAMS)
    )
    return func

def run_preprocessor(func: RunPreProcessor) -> RunPreProcessor:
    '''事件处理器运行前预处理

    装饰一个函数，使其在事件处理器运行之前执行
    '''
    _run_preprocessors.add(
        Dependent[Any].parse(call=func, allow_types=RUN_PREPCS_PARAMS)
    )
    return func

def run_postprocessor(func: RunPostProcessor) -> RunPostProcessor:
    '''事件处理器运行后处理

    装饰一个函数，使其在事件处理器运行之后执行
    '''
    _run_postprocessors.add(
        Dependent[Any].parse(call=func, allow_types=RUN_POSTPCS_PARAMS)
    )
    return func

def _apply_event_preprocessors(
    bot: 'Bot',
    event: 'Event',
    state: StateType,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None,
    show_log: bool = True
) -> bool:
    '''运行事件预处理器

    参数:
        bot (Bot): 机器人对象
        event (Event): 事件对象
        state (StateType): 状态对象
        stack (Optional[ExitStack], 可选): 上下文管理器栈
        dependency_cache (Optional[DependencyCache], 可选): 依赖缓存
        show_log (bool, 可选): 是否显示日志

    返回:
        bool: 是否继续处理事件
    '''
    if not _event_preprocessors:
        return True
    
    if show_log:
        logger.debug('Running event preprocessors...')
    
    try:
        _procs: list[Task] = [
            Task(
                processor,
                bot=bot,
                event=event,
                state=state,
                stack=stack,
                dependency_cache=dependency_cache
            ) for processor in _event_preprocessors
        ]
        gather(
            *(Task(run_with_catch, proc, SkippedException) for proc in _procs)
        )
    except IgnoredException:
        logger.debug(
            f'Event {event.get_event_name()} has been ignored'
        )
        return False
    except Exception as exception:
        logger.error(
            'Error occurred while running event preprocessors',
            exception=exception
        )
        return False
    
    return True

def _apply_event_postprocessors(
    bot: 'Bot',
    event: 'Event',
    state: StateType,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None,
    show_log: bool = True
) -> None:
    '''运行事件后处理器

    参数:
        bot (Bot): 机器人对象
        event (Event): 事件对象
        state (StateType): 状态对象
        stack (Optional[ExitStack], 可选): 上下文管理器栈
        dependency_cache (Optional[DependencyCache], 可选): 依赖缓存
        show_log (bool, 可选): 是否显示日志
    '''
    if not _event_postprocessors:
        return
    
    if show_log:
        logger.debug('Running event postprocessors...')
    
    try:
        _procs: list[Task] = [
            Task(
                processor,
                bot=bot,
                event=event,
                state=state,
                stack=stack,
                dependency_cache=dependency_cache
            ) for processor in _event_postprocessors
        ]
        gather(
            *(Task(run_with_catch, proc, SkippedException) for proc in _procs)
        )
    except Exception as e:
        logger.error(
            'Error occurred while running event postprocessors',
            exception=e
        )

def _apply_run_preprocessors(
    bot: 'Bot',
    event: 'Event',
    state: StateType,
    processor: Processor,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None
) -> bool:
    '''运行事件响应器处理前处理

    参数:
        bot (Bot): 机器人对象
        event (Event): 事件对象
        state (StateType): 状态对象
        processor (Processor): 事件处理器对象
        stack (Optional[ExitStack], 可选): 上下文管理器栈
        dependency_cache (Optional[DependencyCache], 可选): 依赖缓存

    返回:
        bool: 是否继续处理事件
    '''
    if not _run_preprocessors:
        return True
    
    with processor.ensure_context(bot, event):
        try:
            _procs: list[Task] = [
                Task(
                    proc,
                    processor=processor,
                    bot=bot,
                    event=event,
                    state=state,
                    stack=stack,
                    dependency_cache=dependency_cache
                ) for proc in _run_preprocessors
            ]
            gather(
                *(Task(run_with_catch, proc, SkippedException) for proc in _procs)
            )
        except IgnoredException:
            logger.debug(
                f'Event {event.get_event_name()} has been cancelled'
            )
            return False
        except Exception as e:
            logger.error(
                'Error occurred while running run preprocessors',
                exception=e
            )
            return False
    
    return True

def _apply_run_postprocessors(
    bot: 'Bot',
    event: 'Event',
    processor: Processor,
    exception: Optional[Exception] = None,
    stack: Optional[ExitStack] = None,
    dependency_cache: Optional[DependencyCache] = None
) -> None:
    '''运行事件响应器处理后处理

    参数:
        bot (Bot): 机器人对象
        event (Event): 事件对象
        processor (Processor): 事件处理器对象
        exception (Optional[Exception], 可选): 异常对象
        stack (Optional[ExitStack], 可选): 上下文管理器栈
        dependency_cache (Optional[DependencyCache], 可选): 依赖缓存
    '''
    if not _run_postprocessors:
        return
    
    with processor.ensure_context(bot, event):
        try:
            _procs: list[Task] = [
                Task(
                    proc,
                    processor=processor,
                    bot=bot,
                    event=event,
                    exception=exception,
                    stack=stack,
                    dependency_cache=dependency_cache
                ) for proc in _run_postprocessors
            ]
            gather(
                *(Task(run_with_catch, proc, SkippedException) for proc in _procs)
            )
        except Exception as e:
            logger.error(
                'Error occurred while running run preprocessors',
                exception=e
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
    
    if not _apply_run_preprocessors(
        bot=bot,
        event=event,
        state=state,
        processor=processor,
        stack=stack,
        dependency_cache=dependency_cache
    ):
        return
    
    exception = None

    try:
        logger.debug(f'Running processor: {processor}')
        processor.run(bot, event, state, stack, dependency_cache)
    except Exception as e:
        logger.error(f'Error occurred while running processor: {processor}', exception=e)
        exception = e
    
    _apply_run_postprocessors(
        bot=bot,
        event=event,
        processor=processor,
        exception=exception,
        stack=stack,
        dependency_cache=dependency_cache
    )
    
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
    if not _check_processor(
        Processor=Processor,
        bot=bot,
        event=event,
        state=state,
        stack=stack,
        dependency_cache=dependency_cache
    ):
        return
    
    _run_processor(
        Processor=Processor,
        bot=bot,
        event=event,
        state=state,
        stack=stack,
        dependency_cache=dependency_cache
    )

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
        if not _apply_event_preprocessors(
            bot=bot,
            event=event,
            state=state,
            stack=stack,
            dependency_cache=dependency_cache
        ):
            return
        
        try:
            TrieRule.get_value(bot, event, state)
        except Exception as e:
            logger.warn('Error occurred while parsing command', exception=e)
    
        break_flag = False
        for priority in sorted(processors.keys()):
            if break_flag:
                break
            
            if show_log:
                logger.debug(f'Running processors with priority {priority}')
            
            pending_tasks = [
                Task(
                    check_and_run_processor,
                    Processor=processor,
                    bot=bot,
                    event=event,
                    state=state,
                    stack=stack,
                    dependency_cache=dependency_cache
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
        
        _apply_event_postprocessors(bot, event, state, stack, dependency_cache, show_log=show_log)
