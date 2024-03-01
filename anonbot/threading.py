'''AnonBot 包装的 threading 模块'''

import os
from queue import Queue
from concurrent.futures import Future, as_completed
from typing import Any, Tuple, Union, Generic, TypeVar, Callable, Optional, TypeAlias
from threading import (
    Lock as Lock,
    Event as Event,
    Thread as Thread,
    main_thread as main_thread,
    current_thread as current_thread,
)

R = TypeVar('R')

_SyncFutureLike: TypeAlias = Union[
    Callable[..., R],
    Tuple[Callable[..., R], Tuple[Any, ...]],
    Tuple[Callable[..., R], dict[str, Any]],
    Tuple[Callable[..., R], Tuple[Any, ...], dict[str, Any]]
]
_FutureResults: TypeAlias = list[Optional[Union[R, Exception]]]

_current_pool_executor: Optional['ThreadPoolExecutor'] = None

def get_pool_executor() -> 'ThreadPoolExecutor':
    '''获取线程池执行器'''
    global _current_pool_executor
    if _current_pool_executor is None:
        _current_pool_executor = ThreadPoolExecutor.run_executor()
    return _current_pool_executor

def all_tasks() -> list['Task']:
    '''获取所有线程池执行器中的未完成任务'''
    return [task for task in get_pool_executor()._all_tasks if not task.done()]

class Task(Generic[R]):
    '''同步任务类，存储同步函数数据

    当直接调用它时，其表现与直接调用函数无异，只是不再需要重新传入参数。

    若想要并行执行任务，请使用 `anonbot.threading.gather` 函数。

    参数:
        call (Callable[..., Any]): 要执行的函数
        args (Optional[Tuple[Any, ...]]): 函数位置参数
        kwargs (Optional[dict[str, Any]]): 函数关键字参数
    '''
    
    call: Callable[..., R]
    '''要执行的函数'''
    args: Tuple[Any, ...] = ()
    '''函数位置参数'''
    kwargs: dict[str, Any] = {}
    '''函数关键字参数'''
    future: Future[R]
    '''函数的执行结果'''
    thread: Optional[Thread] = None
    '''函数的执行线程'''
    
    def __init__(
        self,
        call: Callable[..., R],
        *args: Any,
        **kwargs: Any
    ) -> None:
        self.call = call
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.future = Future[R]()
    
    def __repr__(self) -> str:
        return f'Task(call={self.call}, args={self.args}, kwargs={self.kwargs})'
    
    def __call__(self) -> Any:
        try:
            result = self.call(*self.args, **self.kwargs)
            self.future.set_result(result)
            return result
        except Exception as exception:
            raise exception
    
    @classmethod
    def _convert(cls, call: _SyncFutureLike[R]) -> 'Task[R]':
        '''将 `_SyncFutureLike` 转换为 `Task`'''
        if callable(call):
            return cls(call)
        elif isinstance(call, tuple):
            func = call[0]
            if len(call) == 2:
                if isinstance(call[1], dict):
                    return cls(func, **call[1])
                else:
                    return cls(func, *call[1])
            elif len(call) == 3:
                return cls(func, *call[1], **call[2])
        raise ValueError('无法将给定的 `_SyncFutureLike` 转换为 `Task`')
    
    def done(self) -> bool:
        '''返回任务是否完成'''
        return self.future.done()
    
    def cancel(self) -> bool:
        '''取消任务'''
        return self.future.cancel()

class ThreadPoolExecutor:
    '''线程池执行器
    
    将会在几个单独的线程中执行任务
    '''
    
    _worker_lock: Lock = Lock()
    _submit_block: bool = False
    _all_tasks: list[Task] = []
    
    def __init__(self, max_workers: Optional[int] = None) -> None:
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        self._tasks: Queue[Task] = Queue()
        self._workers: set[Thread] = set()
        self._main_thread: Optional[Thread] = None
        self._max_workers: int = max_workers
    
    def __repr__(self) -> str:
        return f'ThreadPoolExecutor(max_workers={self._max_workers})'
    
    def _run_workers(self) -> None:
        for _ in range(self._max_workers):
            thread = Thread(target=self._worker, daemon=True)
            thread.start()
            self._workers.add(thread)
    
    @classmethod
    def run_executor(cls, max_workers: Optional[int] = None) -> 'ThreadPoolExecutor':
        executor = cls(max_workers)
        _thread = Thread(target=executor._run_workers, daemon=True)
        _thread.start()
        executor._main_thread = _thread
        return executor
    
    def _worker(self) -> None:
        while True:
            task = self._tasks.get()
            task.thread = current_thread()
            try:
                task()
            except Exception as exception:
                task.future.set_exception(exception)

    def submit(self, task: Task[R]) -> Future[R]:
        '''提交一个任务到线程池执行器'''
        if self._submit_block:
            raise RuntimeError('线程池执行器已关闭')
        with self._worker_lock:
            self._tasks.put(task)
            return task.future
    
    def shutdown(self, wait: bool = True) -> None:
        '''关闭线程池执行器'''
        self._submit_block = True
        if wait:
            for worker in self._workers:
                worker.join()
        self._main_thread.join(0) if self._main_thread is not None else None
    
    def stop(self) -> None:
        '''停止线程池执行器'''
        self.shutdown(wait=False)

def gather(*sync_futures: Union[_SyncFutureLike[R], Task[R]], return_exceptions: bool=False) -> _FutureResults:
    '''并发执行同步任务
    
    `_SyncFutureLike` 是一个用于表示同步任务的类型，
    传入一个元组，元组的第一个元素是一个函数，后面的元素是函数的参数。
    
    位置参数为一个参数元组，而关键字参数为一个关键字参数字典。
    
    该函数仅在所有函数执行完毕后返回结果或抛出异常，请注意。

    参数:
        sync_futures (_SyncFutureLike[R] | Task): 同步任务列表
        return_exceptions (bool): 是否返回异常，默认为 False
    '''
    _futures: dict[Future[R], int] = {}
    result: _FutureResults = [None] * len(sync_futures)
    
    for index, sync_future in enumerate(sync_futures):
        if not isinstance(sync_future, Task):
            sync_future = Task[R]._convert(sync_future)
        if sync_future.thread is None:
            _futures[
                get_pool_executor().submit(sync_future)
            ] = index
        else:
            _futures[sync_future.future] = index
    
    for future in as_completed(_futures):
        try:
            result[_futures[future]] = future.result()
        except Exception as exception:
            if return_exceptions:
                result[_futures[future]] = exception
            else:
                raise exception
    
    return result

def wait_for(task: Task[R], timeout: Optional[float]=None) -> Optional[R]:
    '''等待任务完成
    
    参数:
        task (Task[R]): 要等待的任务
        timeout (Optional[float]): 等待超时时间，默认为无限
    '''
    return task.future.result(timeout)

def create_task(task: Union[Callable[..., R], Task[R]], *args: Any, **kwargs: Any) -> Task[R]:
    '''创建并立刻运行一个任务'''
    if not isinstance(task, Task):
        task = Task[R](task, *args, **kwargs)
    get_pool_executor().submit(task)
    return task
