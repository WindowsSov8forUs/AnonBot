'''AnonBot 日志模块定义'''

import os
import inspect
import logging
from traceback import format_exception
from datetime import datetime, timedelta
from typing import Any, Union, TextIO, Callable, Optional

from rich import print

from .threading import Lock

def link(text: str, url: str) -> str:
    '''生成链接文本'''
    return f'[link={url}]{text}[/link]'

def color(color: str) -> Callable[[str], str]:
    def _colored(text: str) -> str:
        return f'[{color}]{text}[/{color}]'
    return _colored

console_log_format: str = (
    f'{color("gray")("{time}")} - '
    f'{color("cyan")("{name}")} - '
    '{level} - '
)
'''控制台文本格式'''

file_log_format: str = (
    '{time} - '
    '{name} - '
    '{level} - '
)
'''文件文本格式'''

exception_log_format: str = f'\n{color("red on black")("{exception}")}'

level_map = {
    'TRACE': color('bold bright_green')('TRACE'),
    'DEBUG': color('bold bright_yellow')('DEBUG'),
    'INFO': color('bold bright_blue')('INFO'),
    'WARN': color('bold yellow')('WARN'),
    'ERROR': color('bold bright_red')('ERROR'),
    'FATAL': color('bold red')('FATAL')
}

levels = {
    'ALL': 0,
    'TRACE': 10,
    'DEBUG': 20,
    'INFO': 30,
    'WARN': 40,
    'ERROR': 50,
    'FATAL': 60,
    'OFF': 100
}

def _get_time() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _get_file() -> TextIO:
    '''获取日志文件对象，如果不存在则创建'''
    # 检测日志路径是否存在
    if not os.path.exists('log'):
        os.mkdir('log')
    
    # 获取当前日期
    now = datetime.now()
    date_now = now.strftime('%Y-%m-%d')
    # 获取五天前日期
    date_before = (now - timedelta(days=5)).strftime('%Y-%m-%d')
    # 如果存在五天前日志文件则删除
    if os.path.exists(f'log/{date_before}.log'):
        os.remove(f'log/{date_before}.log')
    
    # 获取日志文件对象
    return open(f'log/{date_now}.log', 'a+', encoding='utf-8')

def _get_log_string(*args) -> str:
    '''获取日志字符串'''
    def _convert(arg: Any) -> str:
        '''将对象转换为字符串'''
        if isinstance(arg, str):
            return arg
        try:
            return str(arg)
        except (TypeError, ValueError):
            try:
                return repr(arg)
            except (TypeError, ValueError):
                return '<不支持的内容>'
    
    return ''.join(map(_convert, args))

class LoggingHandler(logging.Handler):
    '''将 logging 模块日志输出转移到自定义日志中'''
    
    def emit(self, record: logging.LogRecord) -> None:
        level = logger.level(record.levelname)
        logger._write(level, record.name, record.getMessage())

class Logger:
    '''日志结构体，同时在控制台和文件中输出日志内容'''
    
    log_level: str = 'INFO'
    
    def __init__(self) -> None:
        self.lock: Lock = Lock()
        '''日志锁'''
        return
    
    def _write(self, level: str, *args, name: str='', exception: Optional[Exception] = None) -> None:
        if levels[level] < levels[self.log_level]:
            return
        
        # 获取引用模块名称
        if name == '':
            module = inspect.getmodule(inspect.stack()[2][0])
            if module is not None:
                name = module.__name__
                if len((_names := name.split('.'))) >= 2 and _names[0] in ('anonbot',):
                    if _names[1] == 'internal':
                        name = '.'.join(_names[2:])
                    name = '.'.join(_names[1:])
            else:
                name = 'unknown'
        
        # 获取日志字符串
        message = _get_log_string(*args)
        # 获取日志时间
        time = _get_time()
        # 获取日志文本
        console_log = console_log_format.format(
            time=time,
            level=level_map[level],
            name=name
        ) + color('white')(message)
        file_log = file_log_format.format(
            time=time,
            level=level,
            name=name
        ) + message
        
        # 添加异常信息
        if exception is not None:
            traceback = ''.join(format_exception(
                type(exception),
                exception,
                exception.__traceback__
            ))
            console_log += exception_log_format.format(exception=traceback)
            file_log += f'\n{traceback}'
        
        # 写入日志
        with self.lock:
            with _get_file() as file:
                print(console_log)
                file.write(file_log + '\n')
    
    def trace(self, *args, **kwargs) -> None:
        '''输出 TRACE 级别日志'''
        self._write('TRACE', *args, **kwargs)
        return
    
    def debug(self, *args, **kwargs) -> None:
        '''输出 DEBUG 级别日志'''
        self._write('DEBUG', *args, **kwargs)
        return
    
    def info(self, *args, **kwargs) -> None:
        '''输出 INFO 级别日志'''
        self._write('INFO', *args, **kwargs)
        return
    
    def warn(self, *args, **kwargs) -> None:
        '''输出 WARN 级别日志'''
        self._write('WARN', *args, **kwargs)
        return
    
    def error(self, *args, **kwargs) -> None:
        '''输出 ERROR 级别日志'''
        self._write('ERROR', *args, **kwargs)
        return
    
    def fatal(self, *args, **kwargs) -> None:
        '''输出 FATAL 级别日志'''
        self._write('FATAL', *args, **kwargs)
        return

    def level(self, name: str) -> str:
        '''转换日志级别'''
        match name:
            case 'NOTSET':
                return 'TRACE'
            case 'DEBUG':
                return 'DEBUG'
            case 'INFO':
                return 'INFO'
            case 'WARNING':
                return 'WARN'
            case 'ERROR':
                return 'ERROR'
            case 'CRITICAL':
                return 'FATAL'
            case _:
                return 'INFO'
    
    def set_level(self, level: Union[str, int]) -> None:
        '''设置日志级别'''
        if isinstance(level, int):
            for name, value in levels.items():
                if value == level:
                    level = name
                    break
            if isinstance(level, int):
                level = 'INFO'
        
        if level not in levels:
            level = self.level(level)
        self.log_level = level

logger = Logger()
'''日志对象'''
