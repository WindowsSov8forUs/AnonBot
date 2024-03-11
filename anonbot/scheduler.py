'''AnonBot 包装的 threading 模块'''

from time import sleep
from datetime import datetime, timedelta
from typing import Tuple, Union, Generic, Literal, TypeVar, Callable, Optional, overload
from threading import (
    Lock as Lock,
    Event as Event,
    Thread as Thread,
    main_thread as main_thread,
    current_thread as current_thread,
)

from anonbot.log import logger
from anonbot.threading import Task, Thread, ThreadPoolExecutor
from anonbot.plugin import _current_plugin_chain

R = TypeVar('R')

class _SchedulerTask(Generic[R]):
    '''定时任务类，存储定时任务数据

    只能通过 `anonbot.threading.Scheduler` 类添加

    参数:
        func (Callable[..., R]): 要执行的函数
        trigger (Literal['interval', 'cron']): 触发器类型
        id (Optional[str]): 任务 ID，默认为函数名称
        max_instance (int): 最大实例数，默认为 `0` 即无上限
    '''
    
    def __init__(
        self,
        func: Callable[..., R],
        trigger: Literal['interval', 'cron'],
        *,
        id: Optional[str] = None,
        max_instance: int = 0
    ) -> None:
        self.func = func
        self.trigger = trigger
        self.id = id or func.__name__
        self.max_instance = max_instance
        self._threads: set[Thread] = set()
        self.cancelled: bool = False
    
    def __repr__(self) -> str:
        return f'SchedulerTask(func={self.func}, trigger={self.trigger}, id={self.id})'
    
    def _run_func(self) -> None:
        try:
            self.func()
        except Exception as exception:
            logger.warn(f'定时任务 {self.id} 执行失败：{exception}')
    
    def _run(self) -> None:
        thread: Thread = Thread(target=self._run_func, daemon=True)
        self._threads.add(thread)
        thread.start()
        thread.join()
        self._threads.remove(thread)
    
    def run_interval(self, interval: int) -> None:
        '''开始运行时间间隔定时任务

        参数:
            interval (int): 时间间隔(秒)
        '''
        _time = datetime.now()
        while True:
            while (datetime.now() - _time).seconds < interval:
                sleep(1)
                if self.cancelled:
                    return
                continue
            _time = datetime.now()
            if self.max_instance and len(self._threads) >= self.max_instance:
                logger.warn(
                    f'定时任务 {self.id} 实例数已达上限，'
                    f'将在 {(_time + timedelta(seconds=interval)).strftime("%Y-%m-%d %H:%M:%S")} 时再次尝试执行。'
                )
            else:
                Thread(target=self._run, daemon=True).start()
            sleep(interval - 0.5)
    
    def run_cron(
        self,
        *,
        second: Optional[Tuple[int, ...]] = None,
        minute: Optional[Tuple[int, ...]] = None,
        hour: Optional[Tuple[int, ...]] = None
    ) -> None:
        def _ensure_cron() -> bool:
            now = datetime.now()
            return any((
                second is not None and now.second in second,
                minute is not None and now.minute in minute,
                hour is not None and now.hour in hour
            ))
        
        def _get_next(target: Tuple[int, ...], now: int) -> int:
            for value in sorted(target):
                if value > now:
                    return value
            return target[0]
        
        while True:
            if self.cancelled:
                return
            now = datetime.now()
            next: datetime = now + timedelta(seconds=1)  # 给 next 变量一个默认值
            if all((second is None, minute is None, hour is None)):
                logger.warn(f'定时任务 {self.id} 未设置任何触发时间，将不会执行。')
                return
            while not _ensure_cron():
                if second is not None:
                    next = now.replace(second=_get_next(second, now.second))
                    if next < now:
                        next = next + timedelta(minutes=1)
                elif minute is not None:
                    next = now.replace(minute=_get_next(minute, now.minute), second=0)
                    if next < now:
                        next = next + timedelta(hours=1)
                elif hour is not None:
                    next = now.replace(hour=_get_next(hour, now.hour), minute=0, second=0)
                    if next < now:
                        next = next + timedelta(days=1)
                sleep((next - datetime.now()).total_seconds())
                if self.cancelled:
                    return
                continue
            if self.max_instance and len(self._threads) >= self.max_instance:
                now = datetime.now()
                next: datetime = now
                if second is not None:
                    next = now.replace(second=_get_next(second, now.second))
                    if next < now:
                        next = next + timedelta(minutes=1)
                elif minute is not None:
                    next = now.replace(minute=_get_next(minute, now.minute), second=0)
                    if next < now:
                        next = next + timedelta(hours=1)
                elif hour is not None:
                    next = now.replace(hour=_get_next(hour, now.hour), minute=0, second=0)
                    if next < now:
                        next = next + timedelta(days=1)
                logger.warn(
                    f'定时任务 {self.id} 实例数已达上限，'
                    f'将在 {next.strftime("%Y-%m-%d %H:%M:%S")} 时再次尝试执行。'
                )
            else:
                Thread(target=self._run, daemon=True).start()
            if second is not None:
                next = now.replace(second=_get_next(second, now.second))
                if next < now:
                    next = next + timedelta(minutes=1)
            elif minute is not None:
                next = now.replace(minute=_get_next(minute, now.minute), second=0)
                if next < now:
                    next = next + timedelta(hours=1)
            elif hour is not None:
                next = now.replace(hour=_get_next(hour, now.hour), minute=0, second=0)
                if next < now:
                    next = next + timedelta(days=1)
            sleep((next - datetime.now()).total_seconds())

    def cancel(self) -> bool:
        '''取消定时任务'''
        self.cancelled = True
        return True
    
    def done(self) -> bool:
        '''返回定时任务是否完成'''
        return self.cancelled

class Scheduler:
    '''定时任务调度器

    每个调度器将单独拥有一个线程池，用以执行定时任务

    由于 Python 的底层运行方式限制，定时任务不宜太多

    定时任务将与主线程池中的任务并行执行，而由于同步多线程的限制，这可能导致资源争抢

    请 **谨慎** 添加定时任务

    参数:
        name (str): 调度器名称
        max_workers (Optional[int]): 线程池最大线程数，默认为 `None`
    '''
    
    def __init__(self, name: str, max_workers: Optional[int] = None) -> None:
        self.name = name
        self.executor = ThreadPoolExecutor.run_executor(max_workers)
        self.tasks: set[_SchedulerTask] = set()
        if plugin_chain := _current_plugin_chain.get():
            plugin_chain[-1].schedulers.add(self)
    
    def __repr__(self) -> str:
        return f'Scheduler(name={self.name}, tasks={len(self.tasks)})'
    
    def _add_job(
        self,
        func: Callable[..., None],
        trigger: Literal['interval', 'cron'],
        *,
        id: Optional[str] = None,
        second: Optional[Union[int, Tuple[int, ...]]] = None,
        minute: Optional[Union[int, Tuple[int, ...]]] = None,
        hour: Optional[Union[int, Tuple[int, ...]]] = None,
        max_instance: int = 0
    ) -> Callable[..., None]:
        if id is None:
            id = func.__name__
        
        if trigger == 'interval':
            interval = 0
            if second is not None and isinstance(second, int):
                interval += second
            elif minute is not None and isinstance(minute, int):
                interval += minute * 60
            elif hour is not None and isinstance(hour, int):
                interval += hour * 3600
            else:
                logger.warn(f'定时任务 {id} 未正确设置任何触发时间，将不会执行。')
                return func
            task = _SchedulerTask(func, trigger, id=id, max_instance=max_instance)
            _task = Task(task.run_interval, interval)
            self.executor.submit(_task)
        elif trigger == 'cron':
            task = _SchedulerTask(func, trigger, id=id, max_instance=max_instance)
            _task = Task(task.run_cron, second=second, minute=minute, hour=hour)
            self.executor.submit(_task)
        else:
            logger.warn(f'定时任务 {id} 未正确设置触发器类型，将不会执行。')
            return func
        self.tasks.add(task)
        return func
    
    @overload
    def task(
        self,
        trigger: Literal['interval'],
        *,
        id: Optional[str] = None,
        second: Optional[int] = None,
        minute: Optional[int] = None,
        hour: Optional[int] = None,
        max_instance: int = 0
    ) -> Callable[[Callable[..., None]], Callable[..., None]]:
        '''时间间隔定时任务装饰器，只能指定一种时间

        参数:
            trigger (Literal[&#39;interval&#39;]): 定时任务策略
            id (Optional[str], optional): 定时任务 ID，默认为函数名称
            second (Optional[int], optional): 时间间隔秒数
            minute (Optional[int], optional): 时间间隔分钟数
            hour (Optional[int], optional): 时间间隔小时数
            max_instance (int, optional): 最大实例数，默认为 `0` 即无上限
        '''
        ...
    
    @overload
    def task(
        self,
        trigger: Literal['cron'],
        *,
        id: Optional[str] = None,
        second: Optional[Tuple[int, ...]] = None,
        minute: Optional[Tuple[int, ...]] = None,
        hour: Optional[Tuple[int, ...]] = None,
        max_instance: int = 0
    ) -> Callable[[Callable[..., None]], Callable[..., None]]:
        '''Cron 定时任务装饰器，只能指定一种时间

        参数:
            trigger (Literal[&#39;cron&#39;]): 定时任务策略
            id (Optional[str], optional): 定时任务 ID，默认为函数名称
            second (Optional[Tuple[int, ...]], optional): 执行秒数
            minute (Optional[Tuple[int, ...]], optional): 执行分钟数
            hour (Optional[Tuple[int, ...]], optional): 执行小时数
            max_instance (int, optional): 最大实例数，默认为 `0` 即无上限
        '''
        ...
    
    def task(
        self,
        trigger: Literal['interval', 'cron'],
        *,
        id: Optional[str] = None,
        second: Optional[Union[int, Tuple[int, ...]]] = None,
        minute: Optional[Union[int, Tuple[int, ...]]] = None,
        hour: Optional[Union[int, Tuple[int, ...]]] = None,
        max_instance: int = 0
    ) -> Callable[[Callable[..., None]], Callable[..., None]]:
        # 内部装饰器
        def _decorator(func: Callable[..., None]) -> Callable[..., None]:
            return self._add_job(
                func,
                trigger,
                id=id,
                second=second,
                minute=minute,
                hour=hour,
                max_instance=max_instance
            )
        return _decorator

    def stop(self) -> None:
        '''终止定时任务调度器'''
        for task in self.tasks:
            task.cancel()
        sleep(1)
        self.executor.stop()
