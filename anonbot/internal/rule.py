from contextlib import ExitStack
from typing import Union, NoReturn, Optional

from anonbot.dependency import Dependent
from anonbot.threading import Task, gather
from anonbot.exception import SkippedException
from anonbot.typing import StateType, RuleChecker, DependencyCache

from .adapter import Bot, Event
from .params import BotParam, EventParam, StateParam, DependParam, DefaultParam

class Rule:
    '''`anonbot.processor.Processor` 规则类'''
    
    __slots__ = ('checkers',)
    
    HANDLER_PARAM_TYPES = [
        DependParam,
        BotParam,
        EventParam,
        StateParam,
        DefaultParam
    ]
    
    def __init__(self, *checkers: Union[RuleChecker, Dependent[bool]]) -> None:
        self.checkers: set[Dependent[bool]] = {
            (
                checker if isinstance(checker, Dependent)
                else Dependent[bool].parse(
                    call=checker, allow_types=self.HANDLER_PARAM_TYPES
                )
            ) for checker in checkers
        }
    
    def __repr__(self) -> str:
        return f'Rule({", ".join(repr(checker) for checker in self.checkers)})'
    
    def __call__(
        self,
        bot: Bot,
        event: Event,
        state: StateType,
        stack: Optional[ExitStack] = None,
        dependency_cache: Optional[DependencyCache] = None
    ) -> bool:
        '''检查是否符合所有规则'''
        try:
            result = gather(
                *(
                    Task(
                        checker,
                        bot=bot,
                        event=event,
                        state=state,
                        stack=stack,
                        dependency_cache=dependency_cache
                    )
                    for checker in self.checkers
                )
            )
        except SkippedException:
            return False
        return all(result)
    
    def __and__(self, other: Optional[Union['Rule', RuleChecker]]) -> 'Rule':
        if other is None:
            return self
        elif isinstance(other, Rule):
            return Rule(*self.checkers, *other.checkers)
        else:
            return Rule(*self.checkers, other)
    
    def __rand__(self, other: Optional[Union['Rule', RuleChecker]]) -> 'Rule':
        if other is None:
            return self
        elif isinstance(other, Rule):
            return Rule(*other.checkers, *self.checkers)
        else:
            return Rule(other, *self.checkers)
    
    def __or__(self, other: object) -> NoReturn:
        raise RuntimeError("Or operation between rules is not allowed.")

