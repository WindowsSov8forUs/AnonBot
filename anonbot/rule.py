'''`anonbot.processor.Processor.rule` 的类型定义'''

import re
from typing import (
    Type,
    Tuple,
    Union,
    TypeVar,
    Optional,
    TypedDict,
    NamedTuple,
    cast
)

from pygtrie import CharTrie

from anonbot.log import logger
from anonbot.internal.rule import Rule as Rule
from anonbot.typing import StateType, CommandStart
from anonbot.adapter import Bot, Event, Message, EventType, MessageSegment
from anonbot.params import Command, EventToMe, CommandArg, CommandWhitespace
from anonbot.consts import (
    CMD_KEY,
    PREFIX_KEY,
    CMD_ARG_KEY,
    KEYWORD_KEY,
    RAW_CMD_KEY,
    ENDSWITH_KEY,
    CMD_START_KEY,
    FULLMATCH_KEY,
    REGEX_MATCHED,
    STARTSWITH_KEY,
    CMD_WHITESPACE_KEY
)

T = TypeVar('T')

class CMD_RESULT(TypedDict):
    command: Optional[str]
    raw_command: Optional[str]
    command_arg: Optional[Message]
    command_start: Optional[str]
    command_whitespace: Optional[str]

class TRIE_VALUE(NamedTuple):
    command_start: str
    command: str

class TrieRule:
    prefix: CharTrie = CharTrie()
    
    @classmethod
    def add_prefix(cls, prefix: str, value: TRIE_VALUE) -> None:
        if prefix in cls.prefix:
            logger.warn(f'Prefix {prefix!r} already exists')
            return
        cls.prefix[prefix] = value
    
    @classmethod
    def get_value(cls, bot: Bot, event: Event, state: StateType) -> CMD_RESULT:
        prefix = CMD_RESULT(
            command=None,
            raw_command=None,
            command_arg=None,
            command_start=None,
            command_whitespace=None
        )
        state[PREFIX_KEY] = prefix
        if event.get_type() != EventType.MESSAGE_CREATED:
            return prefix
        
        message = event.get_message()
        message_seg: MessageSegment = message[0]
        if message_seg.is_text():
            segment_text = str(message_seg).lstrip()
            if pf := cls.prefix.longest_prefix(segment_text):
                value: TRIE_VALUE = pf.value
                prefix[RAW_CMD_KEY] = pf.key
                prefix[CMD_START_KEY] = value.command_start
                prefix[CMD_KEY] = value.command
                
                msg = message.copy()
                msg.pop(0)
                
                arg_str = segment_text[len(pf.key):]
                arg_str_stripped = arg_str.lstrip()
                while not arg_str_stripped and msg and msg[0].is_text():
                    arg_str += str(msg.pop(0))
                    arg_str_stripped = arg_str.lstrip()
                
                has_arg = arg_str_stripped or msg
                if (
                    has_arg
                    and (stripped_len := len(arg_str) - len(arg_str_stripped)) >= 0
                ):
                    prefix[CMD_WHITESPACE_KEY] = arg_str[:stripped_len]
                
                if arg_str_stripped:
                    new_message = msg.__class__(arg_str_stripped)
                    for new_segment in reversed(new_message):
                        msg.insert(0, new_segment)
                prefix[CMD_ARG_KEY] = msg
        return prefix

    @classmethod
    def del_prefix(cls, prefix: str) -> None:
        if prefix in cls.prefix:
            del cls.prefix[prefix]

class StartswithRule:
    '''检查消息纯文本是否以指定字符串开头'''
    
    __slots__ = ('msg', 'ignorecase')
    
    def __init__(self, msg: Tuple[str, ...], ignorecase: bool = False) -> None:
        self.msg = msg
        self.ignorecase = ignorecase
    
    def __repr__(self) -> str:
        return f'Startswith(msg={self.msg}, ignorecase={self.ignorecase})'
    
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, StartswithRule)
            and frozenset(self.msg) == frozenset(other.msg)
            and self.ignorecase == other.ignorecase
        )
    
    def __hash__(self) -> int:
        return hash((frozenset(self.msg), self.ignorecase))
    
    def __call__(self, event: Event, state: StateType) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if match := re.match(
            f'^(?:{"|".join(re.escape(prefix) for prefix in self.msg)})',
            text,
            re.IGNORECASE if self.ignorecase else 0,
        ):
            state[STARTSWITH_KEY] = match.group()
            return True
        return False

def startswith(msg: Union[str, Tuple[str, ...]], ignorecase: bool = False) -> Rule:
    '''检查消息纯文本是否以指定字符串开头'''
    if isinstance(msg, str):
        msg = (msg,)
    return Rule(StartswithRule(msg, ignorecase))

class EndswithRule:
    '''检查消息纯文本是否以指定字符串结尾'''

    __slots__ = ('msg', 'ignorecase')

    def __init__(self, msg: Tuple[str, ...], ignorecase: bool = False):
        self.msg = msg
        self.ignorecase = ignorecase

    def __repr__(self) -> str:
        return f'Endswith(msg={self.msg}, ignorecase={self.ignorecase})'

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, EndswithRule)
            and frozenset(self.msg) == frozenset(other.msg)
            and self.ignorecase == other.ignorecase
        )

    def __hash__(self) -> int:
        return hash((frozenset(self.msg), self.ignorecase))

    def __call__(self, event: Event, state: StateType) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if match := re.search(
            f'(?:{"|".join(re.escape(suffix) for suffix in self.msg)})$',
            text,
            re.IGNORECASE if self.ignorecase else 0,
        ):
            state[ENDSWITH_KEY] = match.group()
            return True
        return False

def endswith(msg: Union[str, Tuple[str, ...]], ignorecase: bool = False) -> Rule:
    '''检查消息纯文本是否以指定字符串结尾'''
    if isinstance(msg, str):
        msg = (msg,)

    return Rule(EndswithRule(msg, ignorecase))

class FullmatchRule:
    '''检查消息纯文本是否完全匹配指定字符串'''
    
    __slots__ = ('msg', 'ignorecase')
    
    def __init__(self, msg: Tuple[str, ...], ignorecase: bool = False) -> None:
        self.msg = tuple(map(str.casefold, msg) if ignorecase else msg)
        self.ignorecase = ignorecase
    
    def __repr__(self) -> str:
        return f'Fullmatch(msg={self.msg}, ignorecase={self.ignorecase})'
    
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FullmatchRule)
            and frozenset(self.msg) == frozenset(other.msg)
            and self.ignorecase == other.ignorecase
        )
    
    def __hash__(self) -> int:
        return hash((frozenset(self.msg), self.ignorecase))
    
    def __call__(self, event: Event, state: StateType) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if not text:
            return False
        text = text.casefold() if self.ignorecase else text
        if text in self.msg:
            state[FULLMATCH_KEY] = text
            return True
        return False

def fullmatch(msg: Union[str, Tuple[str, ...]], ignorecase: bool = False) -> Rule:
    '''检查消息纯文本是否完全匹配指定字符串'''
    if isinstance(msg, str):
        msg = (msg,)
    return Rule(FullmatchRule(msg, ignorecase))

class KeywordsRule:
    '''检查消息纯文本是否包含指定关键词'''
    
    __slots__ = ('keywords',)
    
    def __init__(self, *keywords: str) -> None:
        self.keywords = keywords
    
    def __repr__(self) -> str:
        return f'Keywords(keywords={self.keywords})'
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, KeywordsRule) and frozenset(
            self.keywords
        ) == frozenset(other.keywords)
    
    def __hash__(self) -> int:
        return hash(frozenset(self.keywords))
    
    def __call__(self, event: Event, state: StateType) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if not text:
            return False
        if key := next((k for k in self.keywords if k in text), None):
            state[KEYWORD_KEY] = key
            return True
        return False

def keyword(*keywords: str) -> Rule:
    '''检查消息纯文本是否包含指定关键词'''
    return Rule(KeywordsRule(*keywords))

class CommandRule:
    '''检查消息纯文本是否为指定命令'''
    
    __slots__ = ('cmds', 'command_start', 'force_whitespace')
    
    def __init__(
        self,
        cmds: list[str],
        command_start: Union[CommandStart, Tuple[CommandStart, ...]],
        force_whitespace: Optional[Union[str, bool]] = None
    ) -> None:
        self.cmds = tuple(cmds)
        self.command_start = cast(
            Tuple[CommandStart, ...],
            (command_start,) if type(command_start) is CommandStart else command_start
        )
        self.force_whitespace = force_whitespace
    
    def __repr__(self) -> str:
        return f'Command(cmds={self.cmds})'
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, CommandRule) and frozenset(self.cmds) == frozenset(
            other.cmds
        )
    
    def __hash__(self) -> int:
        return hash((frozenset(self.cmds),))
    
    def __call__(
        self,
        cmd: Optional[str] = Command(),
        cmd_arg: Optional[Message] = CommandArg(),
        cmd_whitespace: Optional[str] = CommandWhitespace(),
    ) -> bool:
        if cmd not in self.cmds:
            return False
        if self.force_whitespace is None or not cmd_arg:
            return True
        if isinstance(self.force_whitespace, str):
            return self.force_whitespace == cmd_whitespace
        return self.force_whitespace == (cmd_whitespace is not None)

def command(
    *cmds: str,
    command_start: Union[CommandStart, Tuple[CommandStart, ...]],
    force_whitespace: Optional[Union[str, bool]] = None
) -> Rule:
    '''检查消息纯文本是否为指定命令'''
    commands: list[str] = []
    command_start = cast(
        Tuple[CommandStart, ...],
        (command_start,) if isinstance(command_start, str) else command_start
    )
    for command in cmds:
        commands.append(command)
        for start in command_start:
            TrieRule.add_prefix(f'{start}{command}', TRIE_VALUE(start, command))
    return Rule(CommandRule(commands, command_start, force_whitespace))

class RegexRule:
    '''检查消息字符串是否符合指定正则表达式'''
    
    __slots__ = ('regex', 'flags')
    
    def __init__(self, regex: str, flags: int = 0):
        self.regex = regex
        self.flags = flags

    def __repr__(self) -> str:
        return f'Regex(regex={self.regex!r}, flags={self.flags})'
    
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, RegexRule)
            and self.regex == other.regex
            and self.flags == other.flags
        )
    
    def __hash__(self) -> int:
        return hash((self.regex, self.flags))

    def __call__(self, event: Event, state: StateType) -> bool:
        try:
            msg = event.get_message()
        except Exception:
            return False
        if matched := re.search(self.regex, str(msg), self.flags):
            state[REGEX_MATCHED] = matched
            return True
        else:
            return False

def regex(regex: str, flags: Union[int, re.RegexFlag] = 0) -> Rule:
    '''检查消息字符串是否符合指定正则表达式'''
    return Rule(RegexRule(regex, flags))

class ToMeRule:
    '''检查事件是否与机器人有关'''
    
    __slots__ = ()
    
    def __repr__(self) -> str:
        return 'ToMe()'
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, ToMeRule)
    
    def __hash__(self) -> int:
        return hash((self.__class__,))
    
    def __call__(self, to_me: bool = EventToMe()) -> bool:
        return to_me

def to_me() -> Rule:
    '''检查事件是否与机器人有关'''
    return Rule(ToMeRule())

class IsTypeRule:
    '''检查事件是否为指定类型'''
    
    __slots__ = ('types',)
    
    def __init__(self, *types: Type[Event]) -> None:
        self.types = types
    
    def __repr__(self) -> str:
        return f'IsType(types={tuple(type.__name__ for type in self.types)})'
    
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, IsTypeRule)
            and self.types == other.types
        )
    
    def __hash__(self) -> int:
        return hash((self.types,))
    
    def __call__(self, event: Event) -> bool:
        return isinstance(event, self.types)

def is_type(*types: Type[Event]) -> Rule:
    '''检查事件是否为指定类型'''
    return Rule(IsTypeRule(*types))

__autodoc__ = {
    'Rule': True,
    'Rule.__call__': True,
    'TrieRule': True,
}
