'''定义了依赖注入的各类参数'''

from typing import Any, Match, Tuple, Optional

from anonbot.typing import StateType
from anonbot.processor import Processor
from anonbot.internal.params import Arg as Arg
from anonbot.adapter import uni, Event, Message
from anonbot.internal.params import ArgStr as ArgStr
from anonbot.internal.params import Depends as Depends
from anonbot.internal.params import ArgParam as ArgParam
from anonbot.internal.params import BotParam as BotParam
from anonbot.internal.params import EventParam as EventParam
from anonbot.internal.params import StateParam as StateParam
from anonbot.internal.params import DependParam as DependParam
from anonbot.internal.params import ArgPlainText as ArgPlainText
from anonbot.internal.params import DefaultParam as DefaultParam
from anonbot.internal.params import ProcessorParam as ProcessorParam
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

def _event_type(event: Event) -> str:
    return event.get_type()

def EventType() -> str:
    '''`anonbot.adapter.Event` 类型参数'''
    return Depends(_event_type)

def _event_message(event: Event) -> Message:
    return event.get_message()

def EventMessage() -> Any:
    '''`anonbot.adater.Event` 消息参数'''
    return Depends(_event_message)

def _event_latform(event: Event) -> str:
    return event.get_platform()

def EventPlatform() -> str:
    '''`anonbot.adapter.Event` 平台参数'''
    return Depends(_event_latform)

def _event_plain_text(event: Event) -> str:
    return event.get_plaintext()

def EventPlainText() -> str:
    '''`anonbot.adapter.Event` 纯文本消息参数'''
    return Depends(_event_plain_text)

def _event_to_me(event: Event) -> bool:
    return event.is_tome()

def EventToMe() -> bool:
    '''`anonbot.adapter.Event` `to_me` 参数'''
    return Depends(_event_to_me)

def _uni_message(event: Event) -> uni.Message:
    return event.get_uni_message()

def UniMessage() -> uni.Message:
    '''`anonbot.adapter.Event` 通用消息参数'''
    return Depends(_uni_message)

def _command(state: StateType) -> Message:
    return state[PREFIX_KEY][CMD_KEY]

def Command() -> str:
    '''消息命令'''
    return Depends(_command)

def _raw_command(state: StateType) -> Message:
    return state[PREFIX_KEY][RAW_CMD_KEY]

def RawCommand() -> str:
    '''消息命令文本'''
    return Depends(_raw_command)

def _command_arg(state: StateType) -> Message:
    return state[PREFIX_KEY][CMD_ARG_KEY]

def CommandArg() -> Message:
    '''消息命令参数'''
    return Depends(_command_arg)

def _command_start(state: StateType) -> str:
    return state[PREFIX_KEY][CMD_START_KEY]

def CommandStart() -> str:
    '''消息命令开头'''
    return Depends(_command_start)

def _command_whitespace(state: StateType) -> str:
    return state[PREFIX_KEY][CMD_WHITESPACE_KEY]

def CommandWhitespace() -> str:
    '''消息命令与参数间的空白'''
    return Depends(_command_whitespace)

def _regex_matched(state: StateType) -> Match[str]:
    return state[REGEX_MATCHED]

def RegexMatched() -> Match[str]:
    '''正则匹配结果'''
    return Depends(_regex_matched, use_cache=False)

def _regex_str(state: StateType) -> str:
    return _regex_matched(state).group()

def RegexStr() -> str:
    '''正则匹配结果文本'''
    return Depends(_regex_str, use_cache=False)

def _regex_group(state: StateType) -> Tuple[Any, ...]:
    return _regex_matched(state).groups()

def RegexGroup() -> Tuple[Any, ...]:
    '''正则匹配结果元组'''
    return Depends(_regex_group, use_cache=False)

def _regex_dict(state: StateType) -> dict[str, Any]:
    return _regex_matched(state).groupdict()

def RegexDict() -> dict[str, Any]:
    '''正则匹配结果字典'''
    return Depends(_regex_dict, use_cache=False)

def _startswith(state: StateType) -> str:
    return state[STARTSWITH_KEY]

def Startswith() -> str:
    '''响应消息开头'''
    return Depends(_startswith, use_cache=False)

def _endswith(state: StateType) -> str:
    return state[ENDSWITH_KEY]

def Endswith() -> str:
    '''响应消息结尾'''
    return Depends(_endswith, use_cache=False)

def _fullmatch(state: StateType) -> str:
    return state[FULLMATCH_KEY]

def Fullmatch() -> str:
    '''完全匹配的消息'''
    return Depends(_fullmatch, use_cache=False)

def _keyword(state: StateType) -> str:
    return state[KEYWORD_KEY]

def Keyword() -> str:
    '''关键词'''
    return Depends(_keyword, use_cache=False)

def Received(id: Optional[str] = None, default: Any = None) -> Any:
    '''`receive` 事件参数'''
    
    def _received(processor: 'Processor') -> Any:
        return processor.get_receive(id or '', default)
    return Depends(_received, use_cache=False)

def LastReceived(default: Any = None) -> Any:
    '''`last_receive` 事件参数'''
    def _last_received(processor: 'Processor') -> Any:
        return processor.get_last_receive(default)
    return Depends(_last_received, use_cache=False)

__autodoc__ = {
    'Arg': True,
    'ArgStr': True,
    'Depends': True,
    'ArgParam': True,
    'BotParam': True,
    'EventParam': True,
    'StateParam': True,
    'DependParam': True,
    'ArgPlainText': True,
    'DefaultParam': True,
    'ProcessorParam': True
}
