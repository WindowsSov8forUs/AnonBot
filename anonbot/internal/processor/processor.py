import sys
import inspect
from pathlib import Path
from types import ModuleType
from dataclasses import dataclass
from contextvars import ContextVar
from datetime import datetime, timedelta
from contextlib import ExitStack, contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    Type,
    Tuple,
    Union,
    TypeVar,
    Callable,
    ClassVar,
    Iterable,
    NoReturn,
    Optional,
    overload
)

from anonbot.log import logger
from anonbot.internal.rule import Rule
from anonbot.utils import classproperty
from anonbot.dependency import Param, Dependent
from anonbot.internal.permission import User, Permission
from anonbot.internal.adapter import (
    Bot,
    Event,
    Message,
    EventType,
    MessageSegment
)
from anonbot.typing import (
    StateType,
    HandlerType,
    TypeUpdater,
    DependencyCache,
    PermissionUpdater
)
from anonbot.consts import (
    ARG_KEY,
    RECEIVE_KEY,
    REJECT_TARGET,
    LAST_RECEIVE_KEY,
    REJECT_CACHE_TARGET
)
from anonbot.exception import (
    PausedException,
    StopPropagation,
    SkippedException,
    FinishedException,
    RejectedException
)
from anonbot.internal.params import (
    Depends,
    ArgParam,
    BotParam,
    EventParam,
    StateParam,
    DependParam,
    DefaultParam,
    ProcessorParam
)

from . import processors

if TYPE_CHECKING:
    from anonbot.plugin import Plugin

T = TypeVar('T')

current_bot: ContextVar[Bot] = ContextVar('current_bot')
current_event: ContextVar[Event] = ContextVar('current_event')
current_processor: ContextVar['Processor'] = ContextVar('current_processor')
current_handler: ContextVar[Dependent] = ContextVar('current_handler')

@dataclass
class ProcessorSource:
    plugin_name: Optional[str] = None
    '''事件处理器所属的插件名'''
    module_name: Optional[str] = None
    '''事件处理器所属的模块路径名'''
    lineno: Optional[int] = None
    '''事件处理器的所在行号'''
    
    @property
    def plugin(self) -> Optional['Plugin']:
        '''事件处理器所属的插件'''
        from anonbot.plugin import get_plugin
        
        if self.plugin_name is not None:
            return get_plugin(self.plugin_name)
    
    @property
    def module(self) -> Optional[ModuleType]:
        if self.module_name is not None:
            return sys.modules.get(self.module_name)
    
    @property
    def file(self) -> Optional[Path]:
        if self.module is not None and (file := inspect.getsourcefile(self.module)):
            return Path(file).absolute()

class ProcessorMeta(type):
    if TYPE_CHECKING:
        type: str
        _source: Optional[ProcessorSource]
        module_name: Optional[str]
    
    def __repr__(self) -> str:
        return (
            f'{self.__name__}(type={self.type!r}'
            + (f', module={self.module_name}' if self.module_name else '')
            + (
                f', lineno={self._source.lineno}'
                if self._source is not None and self._source.lineno is not None
                else ''
            )
            + ')'
        )

class Processor(metaclass=ProcessorMeta):
    '''事件处理器类'''
    
    _source: ClassVar[Optional[ProcessorSource]] = None
    
    type: ClassVar[str] = ''
    '''事件处理器类型'''
    rule: ClassVar[Rule] = Rule()
    '''匹配规则'''
    permission: ClassVar[Permission] = Permission()
    '''触发权限'''
    handlers: list[Dependent[Any]] = []
    '''处理函数列表'''
    priority: ClassVar[int] = 1
    '''优先级'''
    block: bool = False
    '''是否阻塞'''
    temp: ClassVar[bool] = False
    '''是否临时'''
    expire_time: ClassVar[Optional[datetime]] = None
    '''过期时间'''
    
    _default_state: ClassVar[StateType] = {}
    '''事件处理器默认状态'''
    
    _default_type_updater: ClassVar[Optional[Dependent[str]]] = None
    '''默认类型更新器'''
    _default_permission_updater: ClassVar[Optional[Dependent[Permission]]] = None
    '''默认权限更新器'''
    
    HANDLER_PARAM_TYPES: ClassVar[Tuple[Type[Param], ...]] = (
        DependParam,
        BotParam,
        EventParam,
        StateParam,
        ArgParam,
        ProcessorParam,
        DefaultParam,
    )
    
    def __init__(self) -> None:
        self.state = self._default_state.copy()
    
    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(type={self.type!r}'
            + (f', module={self.module_name}' if self.module_name else '')
            + (
                f', lineno={self._source.lineno}' if self._source and self._source.lineno is not None
                else ''
            )
            + ')'
        )
    
    @classmethod
    def new(
        cls,
        type_: Union[EventType, str] = '',
        rule: Optional[Rule] = None,
        permission: Optional[Permission] = None,
        handlers: Optional[list[Union[HandlerType, Dependent[Any]]]] = None,
        temp: bool = False,
        priority: int = 1,
        block: bool = False,
        *,
        source: Optional[ProcessorSource] = None,
        expire_time: Optional[Union[datetime, timedelta]] = None,
        default_state: Optional[StateType] = None,
        default_type_updater: Optional[Union[TypeUpdater, Dependent[str]]] = None,
        default_permission_updater: Optional[Union[PermissionUpdater, Dependent[Permission]]] = None
    ) -> Type[Self]:
        '''创建一个新的事件处理器，并存储'''
        NewProcessor = type(
            cls.__name__,
            (cls,),
            {
                '_source': source,
                'type': type_,
                'rule': rule or Rule(),
                'permission': permission or Permission(),
                'handlers': [
                    handler if isinstance(handler, Dependent)
                    else Dependent[Any].parse(
                        call=handler, allow_types=cls.HANDLER_PARAM_TYPES
                    ) for handler in handlers
                ]
                if handlers else [],
                'temp': temp,
                'expire_time': (
                    expire_time and (
                        expire_time if isinstance(expire_time, datetime)
                        else datetime.now() + expire_time
                    )
                ),
                'priority': priority,
                'block': block,
                '_default_state': default_state or {},
                '_default_type_updater': (
                    default_type_updater and (
                        default_type_updater if isinstance(default_type_updater, Dependent)
                        else Dependent[str].parse(
                            call=default_type_updater, allow_types=cls.HANDLER_PARAM_TYPES
                        )
                    )
                ),
                '_default_permission_updater': (
                    default_permission_updater and (
                        default_permission_updater if isinstance(default_permission_updater, Dependent)
                        else Dependent[Permission].parse(
                            call=default_permission_updater, allow_types=cls.HANDLER_PARAM_TYPES
                        )
                    )
                )
            }
        )
        
        logger.trace(f'创建新的事件处理器：{NewProcessor}')
        processors[priority].append(NewProcessor)
        
        return NewProcessor # type: ignore
    
    @classmethod
    def destroy(cls) -> None:
        '''销毁事件处理器'''
        processors[cls.priority].remove(cls)
    
    @classproperty
    def plugin(cls) -> Optional['Plugin']:
        '''事件处理器所属的插件'''
        return cls._source and cls._source.plugin
    
    @classproperty
    def module(cls) -> Optional[ModuleType]:
        '''事件处理器所属的模块'''
        return cls._source and cls._source.module
    
    @classproperty
    def plugin_name(cls) -> Optional[str]:
        '''事件处理器所属的插件名'''
        return cls._source and cls._source.plugin_name
    
    @classproperty
    def module_name(cls) -> Optional[str]:
        '''事件处理器所属的模块名'''
        return cls._source and cls._source.module_name
    
    @classmethod
    def check_perm(
        cls,
        bot: Bot,
        event: Event,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> bool:
        '''检查是否满足触发权限'''
        event_type = event.get_type()
        return event_type == (cls.type or event_type) and cls.permission(bot, event, stack, dependency_cache)
    
    @classmethod
    def check_rule(
        cls,
        bot: Bot,
        event: Event,
        state: StateType,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> bool:
        '''检查是否满足匹配规则'''
        event_type = event.get_type()
        return event_type == (cls.type or event_type) and cls.rule(bot, event, state, stack, dependency_cache)
    
    @classmethod
    def type_updater(cls, func: TypeUpdater) -> TypeUpdater:
        '''类型更新器装饰器'''
        cls._default_type_updater = Dependent[str].parse(
            call=func, allow_types=cls.HANDLER_PARAM_TYPES
        )
        return func
    
    @classmethod
    def permission_updater(cls, func: PermissionUpdater) -> PermissionUpdater:
        '''权限更新器装饰器'''
        cls._default_permission_updater = Dependent[Permission].parse(
            call=func, allow_types=cls.HANDLER_PARAM_TYPES
        )
        return func
    
    @classmethod
    def append_handler(cls, handler: HandlerType, parameterless: Optional[Iterable[Any]] = None) -> Dependent[Any]:
        '''添加处理函数'''
        handler_ = Dependent[Any].parse(
            call=handler,
            parameterless=parameterless,
            allow_types=cls.HANDLER_PARAM_TYPES
        )
        cls.handlers.append(handler_)
        return handler_
    
    @classmethod
    def handle(cls, parameterless: Optional[Iterable[Any]] = None) -> Callable[[HandlerType], HandlerType]:
        '''处理函数装饰器'''
        def _decorator(handler: HandlerType) -> HandlerType:
            cls.append_handler(handler, parameterless=parameterless)
            return handler
        return _decorator
    
    @classmethod
    def receive(cls, id: str = '', parameterless: Optional[Iterable[Any]] = None) -> Callable[[HandlerType], HandlerType]:
        '''在接收用户新的消息后运行该函数'''
        
        def _receive(event: Event, processor: 'Processor') -> Union[None, NoReturn]:
            processor.set_target(RECEIVE_KEY.format(id=id))
            if processor.get_target() == RECEIVE_KEY.format(id=id):
                processor.set_receive(id, event)
                return
            if processor.get_receive(id, ...) is not ...:
                return
            processor.reject()
        
        _parameterless = (Depends(_receive), *(parameterless or ()))
        
        def _decorator(call: HandlerType) -> HandlerType:
            if cls.handlers and cls.handlers[-1].call is call:
                handler = cls.handlers[-1]
                new_handler = Dependent(
                    call=handler.call,
                    params=handler.params,
                    parameterless=Dependent.parse_parameterless(
                        tuple(_parameterless), cls.HANDLER_PARAM_TYPES
                    ) + handler.parameterless
                )
                cls.handlers[-1] = new_handler
            else:
                cls.append_handler(call, parameterless=_parameterless)
            return call
        return _decorator
    
    @classmethod
    def get(cls, key: str, prompt: Optional[Union[str, Message, MessageSegment]] = None, parameterless: Optional[Iterable[Any]] = None) -> Callable[[HandlerType], HandlerType]:
        '''装饰一个函数来获取指定参数 `key`'''
        
        def _key_getter(event: Event, processor: 'Processor') -> None:
            processor.set_target(ARG_KEY.format(key=key))
            if processor.get_target() == ARG_KEY.format(key=key):
                processor.set_arg(key, event.get_message())
                return
            if processor.get_arg(key, ...) is not ...:
                return
            processor.reject(prompt)
        
        parameterless = (Depends(_key_getter), *(parameterless or ()))
        
        def _decorator(call: HandlerType) -> HandlerType:
            if cls.handlers and cls.handlers[-1].call is call:
                handler = cls.handlers[-1]
                new_handler = Dependent(
                    call=handler.call,
                    params=handler.params,
                    parameterless=Dependent.parse_parameterless(
                        tuple(parameterless), cls.HANDLER_PARAM_TYPES
                    ) + handler.parameterless
                )
                cls.handlers[-1] = new_handler
            else:
                cls.append_handler(call, parameterless=parameterless)
            return call
        return _decorator
    
    @classmethod
    def send(cls, message: Union[str, Message, MessageSegment], **kwargs: Any) -> Any:
        '''发送消息'''
        bot = current_bot.get()
        event = current_event.get()
        return bot.send(event, message, **kwargs)
    
    @classmethod
    def finish(cls, message: Optional[Union[str, Message, MessageSegment]] = None, **kwargs: Any) -> NoReturn:
        '''发送一条消息并结束当前事件处理'''
        if message is not None:
            cls.send(message, **kwargs)
        raise FinishedException
    
    @classmethod
    def next(cls, prompt: Optional[Union[str, Message, MessageSegment]] = None, **kwargs: Any) -> NoReturn:
        '''发送一条消息，在接受新的消息后继续下一个处理函数'''
        if prompt is not None:
            cls.send(prompt, **kwargs)
        raise PausedException
    
    @classmethod
    def reject(cls, prompt: Optional[Union[str, Message, MessageSegment]] = None, **kwargs: Any) -> NoReturn:
        '''最近通过 `get` 或 `receive` 接收的消息不满足条件，等待下一条消息后重新运行当前处理函数'''
        if prompt is not None:
            cls.send(prompt, **kwargs)
        raise RejectedException
    
    @classmethod
    def reject_arg(cls, key: str, prompt: Optional[Union[str, Message, MessageSegment]] = None, **kwargs: Any) -> NoReturn:
        '''指定的 `get` 消息不满足条件，等待下一条消息后重新运行当前处理函数'''
        processor = current_processor.get()
        processor.set_target(ARG_KEY.format(key=key))
        if prompt is not None:
            cls.send(prompt, **kwargs)
        raise RejectedException
    
    @classmethod
    def reject_receive(cls, id: str = '', prompt: Optional[Union[str, Message, MessageSegment]] = None, **kwargs: Any) -> NoReturn:
        '''指定的 `receive` 消息不满足条件，等待下一条消息后重新运行当前处理函数'''
        processor = current_processor.get()
        processor.set_target(RECEIVE_KEY.format(id=id))
        if prompt is not None:
            cls.send(prompt, **kwargs)
        raise RejectedException
    
    @classmethod
    def skip(cls) -> NoReturn:
        '''跳过当前处理函数'''
        raise SkippedException
    
    @overload
    def get_receive(self, id: str) -> Union[Event, None]:
        ...
    
    @overload
    def get_receive(self, id: str, default: T) -> Union[Event, T]:
        ...
    
    def get_receive(self, id: str, default: Optional[T] = None) -> Optional[Union[Event, T]]:
        '''获取一个 `receive` 消息'''
        return self.state.get(RECEIVE_KEY.format(id=id), default)
    
    def set_receive(self, id: str, event: Event) -> None:
        '''设置一个 `receive` 事件'''
        self.state[RECEIVE_KEY.format(id=id)] = event
        self.state[LAST_RECEIVE_KEY] = event
    
    @overload
    def get_last_receive(self) -> Union[Event, None]:
        ...
    
    @overload
    def get_last_receive(self, default: T) -> Union[Event, T]:
        ...
    
    def get_last_receive(self, default: Optional[T] = None) -> Optional[Union[Event, T]]:
        '''获取最后一个 `receive` 事件'''
        return self.state.get(LAST_RECEIVE_KEY, default)
    
    @overload
    def get_arg(self, key: str) -> Union[Message, None]:
        ...
    
    @overload
    def get_arg(self, key: str, default: T) -> Union[Message, T]:
        ...
    
    def get_arg(self, key: str, default: Optional[T] = None) -> Optional[Union[Message, T]]:
        '''获取一个 `get` 消息'''
        
        return self.state.get(ARG_KEY.format(key=key), default)
    
    def set_arg(self, key: str, message: Message) -> None:
        '''设置一个 `get` 消息'''
        self.state[ARG_KEY.format(key=key)] = message
    
    def set_target(self, target: str, cache: bool = True) -> None:
        if cache:
            self.state[REJECT_CACHE_TARGET] = target
        else:
            self.state[REJECT_TARGET] = target
    
    @overload
    def get_target(self) -> Union[str, None]:
        ...
    
    @overload
    def get_target(self, default: T) -> Union[str, T]:
        ...
    
    def get_target(self, default: Optional[T] = None) -> Optional[Union[str, T]]:
        return self.state.get(REJECT_TARGET, default)
    
    def stop(self) -> None:
        '''停止事件处理'''
        self.block = True
    
    def update_type(
        self,
        bot: Bot,
        event: Event,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> str:
        updater = self.__class__._default_type_updater
        return (
            updater(
                bot=bot,
                event=event,
                state=self.state,
                processor=self,
                stack=stack,
                dependency_cache=dependency_cache
            ) if updater else 'message'
        )
    
    def update_permission(
        self,
        bot: Bot,
        event: Event,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> Permission:
        if updater := self.__class__._default_permission_updater:
            return updater(
                bot=bot,
                event=event,
                state=self.state,
                processor=self,
                stack=stack,
                dependency_cache=dependency_cache
            )
        return Permission(User.from_event(event, perm=self.permission))
    
    def resolve_reject(self) -> None:
        handler = current_handler.get()
        self.handlers.insert(0, handler)
        if REJECT_CACHE_TARGET in self.state:
            self.state[REJECT_TARGET] = self.state.pop(REJECT_CACHE_TARGET)
    
    @contextmanager
    def ensure_context(self, bot: Bot, event: Event) -> Any:
        bot_ = current_bot.set(bot)
        event_ = current_event.set(event)
        processor_ = current_processor.set(self)
        try:
            yield
        finally:
            current_bot.reset(bot_)
            current_event.reset(event_)
            current_processor.reset(processor_)
    
    def _run(
        self,
        bot: Bot,
        event: Event,
        state: StateType,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> None:
        logger.trace(
            f'运行 {self}: '
            f'bot={bot}, event={event!r}, state={state!r}'
        )
        
        with self.ensure_context(bot, event):
            try:
                self.state.update(state)
                
                while self.handlers:
                    handler = self.handlers.pop(0)
                    current_handler.set(handler)
                    logger.debug(f'运行处理函数 {handler}')
                    try:
                        handler(
                            processor=self,
                            bot=bot,
                            event=event,
                            state=self.state,
                            stack=stack,
                            dependency_cache=dependency_cache
                        )
                    except SkippedException:
                        logger.debug(f'处理函数 {handler} 被跳过')
            except StopPropagation:
                self.block = True
            finally:
                logger.debug(f'{self} 运行结束')
    
    def run(
        self,
        bot: Bot,
        event: Event,
        state: StateType,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> None:
        '''运行事件处理器'''
        try:
            self._run(bot, event, state, stack, dependency_cache)
        except RejectedException:
            self.resolve_reject()
            type_ = self.update_type(bot, event, stack, dependency_cache)
            permission = self.update_permission(bot, event, stack, dependency_cache)
            
            self.new(
                type_,
                Rule(),
                permission,
                self.handlers,
                temp=True,
                priority=0,
                block=True,
                source=self.__class__._source,
                expire_time=bot.config.session_expire_timeout,
                default_state=self.state,
                default_type_updater=self.__class__._default_type_updater,
                default_permission_updater=self.__class__._default_permission_updater
            )
        except PausedException:
            type_ = self.update_type(bot, event, stack, dependency_cache)
            permission = self.update_permission(bot, event, stack, dependency_cache)
            
            self.new(
                type_,
                Rule(),
                permission,
                self.handlers,
                temp=True,
                priority=0,
                block=True,
                source=self.__class__._source,
                expire_time=bot.config.session_expire_timeout,
                default_state=self.state,
                default_type_updater=self.__class__._default_type_updater,
                default_permission_updater=self.__class__._default_permission_updater
            )
        except FinishedException:
            pass
