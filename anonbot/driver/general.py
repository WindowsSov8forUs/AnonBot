'''总驱动器'''

import signal
from time import sleep
from typing_extensions import override

from anonbot import console
from anonbot import threading
from anonbot.log import logger
from anonbot.config import Config
from anonbot.consts import WINDOWS
from anonbot.driver import Driver as BaseDriver

from ._lifespan import LIFESPAN_FUNC, Lifespan

HANDLED_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM
)
if WINDOWS: # pragma: py-win32
    HANDLED_SIGNALS += (signal.SIGBREAK,)

class Driver(BaseDriver):
    '''总驱动器'''
    
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        
        self._lifespan: Lifespan = Lifespan()
        
        self.should_exit: threading.Event = threading.Event()
        self.force_exit: bool = False
    
    @property
    @override
    def type(self) -> str:
        return 'general'
    
    @override
    def on_startup(self, func: LIFESPAN_FUNC) -> LIFESPAN_FUNC:
        return self._lifespan.on_startup(func)
    
    @override
    def on_shutdown(self, func: LIFESPAN_FUNC) -> LIFESPAN_FUNC:
        return self._lifespan.on_shutdown(func)
    
    @override
    def run(self, *args, **kwargs) -> None:
        '''启动总驱动'''
        super().run(*args, **kwargs)
        self._serve()
    
    def _serve(self) -> None:
        self._install_signal_handlers()
        self._startup()
        if self.should_exit.is_set():
            return
        self._main_thread()
        self._shutdown()
    
    def _startup(self) -> None:
        try:
            self._lifespan.startup()
        except Exception as exception:
            logger.error('Lifespan 启动失败', exception=exception)
        
        logger.info('应用启动成功')
        console.run(self)
    
    def _main_thread(self) -> None:
        while not self.should_exit.is_set():
            sleep(0.1)
    
    def _shutdown(self) -> None:
        logger.info('应用退出中...')
        
        try:
            self._lifespan.shutdown()
        except Exception as exception:
            logger.error('Lifespan 退出失败', exception=exception)
        
        for task in threading.all_tasks():
            if not task.done():
                task.cancel()
        sleep(0.1)
        
        tasks = threading.all_tasks()
        if tasks and not self.force_exit:
            logger.info('正在等待所有任务完成... (Ctrl+C 可强制退出)')
        while tasks and not self.force_exit:
            sleep(0.1)
            tasks = threading.all_tasks()
        
        for task in tasks:
            task.cancel(True)
        
        logger.info('应用退出成功')
        executor = threading.get_pool_executor()
        executor.stop()
    
    def _install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return
        
        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self._handle_exit)
    
    def _handle_exit(self, sig: int, frame: object) -> None:
        '''处理退出信号'''
        self.exit(force=self.should_exit.is_set())
    
    def exit(self, force: bool = False) -> None:
        '''退出总驱动

        参数:
            force (bool): 是否强制退出
        '''
        if not self.should_exit.is_set():
            self.should_exit.set()
        if force:
            self.force_exit = True
