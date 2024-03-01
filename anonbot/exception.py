'''AnonBot 异常模块定义'''

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from anonbot.dependency.utils import ParameterField

class AnonBotException(Exception):
    '''AnonBot 异常基类'''
    def __str__(self) -> str:
        return self.__repr__()

class ProcessException(AnonBotException):
    '''AnonBot 事件处理异常基类'''

class SkippedException(ProcessException):
    '''指示 AnonBot 结束当前 `Dependent` 运行'''

class TypeMisMatch(SkippedException):
    '''当前 `Handler` 参数类型不匹配'''
    
    def __init__(self, param: 'ParameterField', value: Any) -> None:
        self.param: ParameterField = param
        self.value: Any = value
    
    def __repr__(self) -> str:
        return (
            f'TypeMisMatch(param={self.param}, '
            f'type={self.param.type_}, value={self.value!r})'
        )

class StopPropagation(ProcessException):
    '''指示 AnonBot 结束当前事件处理'''

class ProcessorException(AnonBotException):
    '''AnonBot 事件处理器异常基类'''

class PausedException(ProcessorException):
    '''指示 AnonBot 结束当前处理函数并等待下一条消息后运行下一个处理函数'''

class RejectedException(ProcessorException):
    '''指示 AnonBot 结束当前处理函数并等待下一条消息后运行当前处理函数'''

class FinishedException(ProcessorException):
    '''指示 AnonBot 结束当前处理流程'''

class DriverException(AnonBotException):
    '''AnonBot 驱动异常基类'''

class WebSocketClosed(DriverException):
    '''WebSocket 已关闭'''
    def __init__(self, code: int, reason: str) -> None:
        self.code = code
        self.reason = reason
    
    def __repr__(self) -> str:
        return f'WebSocketClosed({self.code}, {self.reason})'

class AdapterException(AnonBotException):
    '''AnonBot 适配器异常基类

    参数:
        adapter (str): 适配器名称
    '''
    
    def __init__(self, adapter: str, *args: object) -> None:
        super().__init__(*args)
        self.adapter: str = adapter

class NoLogException(AdapterException):
    '''指示 AnonBot 不记录日志'''
