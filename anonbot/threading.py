'''AnonBot 包装的 threading 模块'''

import os
import time
import inspect
from queue import Queue
from concurrent.futures._base import CANCELLED
from concurrent.futures import Future, as_completed
from typing import Any, Tuple, Union, Generic, TypeVar, Callable, NoReturn, Optional, TypeAlias
from threading import (
    Lock as Lock,
    Event as Event,
    Thread as Thread,
    main_thread as main_thread,
    current_thread as current_thread
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

def _Thread(*, target: Callable[..., Any], **kwargs: Any) -> Thread:
    '''创建一个线程
    
    参数:
        target (Callable[..., Any]): 要执行的函数
        args (Any): 函数位置参数
        kwargs (Any): 函数关键字参数
    '''
    thread = Thread(target=target, **kwargs)
    thread.__setattr__('__stop_signal', Event())
    return thread

def loop(func: Callable[..., None]) -> Callable[..., NoReturn]:
    '''循环装饰器

    使函数循环执行。

    参数:
        func (Callable[..., None]): 要执行的循环函数，该函数不能有返回值，且理应永久执行
    '''
    def _decorator(*args: Any, **kwargs: Any) -> NoReturn:
        _signal: Optional[Event] = getattr(current_thread(), '__stop_signal', None)
        while _signal is None or not _signal.is_set():
            func(*args, **kwargs)
        raise CancelledError(f'This thread {current_thread().getName()} has been cancelled.')
    return _decorator

def sleep(seconds: float, /) -> None:
    '''线程休眠

    若休眠时任务被取消则立即停止休眠并抛出错误

    参数:
        seconds (float): 休眠时间
    '''
    _signal: Optional[Event] = getattr(current_thread(), '__stop_signal', None)
    if _signal is not None:
        if _signal.wait(seconds):
            raise CancelledError(f'This thread {current_thread().getName()} has been cancelled.')
    else:
        time.sleep(seconds)

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
    signature: inspect.Signature
    '''函数签名'''
    args: Tuple[Any, ...] = ()
    '''函数位置参数'''
    kwargs: dict[str, Any] = {}
    '''函数关键字参数'''
    bound_args: inspect.BoundArguments
    '''函数绑定参数'''
    future: Future[R]
    '''函数的执行结果 `concurrent.futures.Future`'''
    thread: Optional[Thread] = None
    '''函数的执行线程'''
    
    def __init__(
        self,
        call: Callable[..., R],
        *args: Any,
        **kwargs: Any
    ) -> None:
        self.call = call
        self.signature = inspect.signature(call)
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.future = Future[R]()
        
        # 检查参数是否符合函数签名
        self.bound_args = self.signature.bind(*args, **kwargs)
        self.bound_args.apply_defaults()
    
    def __repr__(self) -> str:
        return (
            f'Task(call={self.call!r}'
            + (f', args=({", ".join(repr(arg) for arg in self.args)})' if self.args else '')
            + (f', kwargs=({", ".join(f"{key}={value!r}" for key, value in self.kwargs.items())})' if self.kwargs else '')
            + ')'
        )
    
    def __str__(self) -> str:
        return (f'Task(call={self.__call_repr__()})')
    
    def __call__(self) -> Union[R, BaseException]:
        try:
            self.run()
            if (exception := self.future.exception()) is not None:
                return exception
            return self.future.result()
        except Exception as exception:
            raise exception
    
    def run(self) -> None:
        if not self.future.set_running_or_notify_cancel():
            return
        
        self.thread = current_thread()
        
        try:
            result = self.call(*self.args, **self.kwargs)
        except BaseException as exception:
            self.future.set_exception(exception)
        else:
            self.future.set_result(result)
    
    def __call_repr__(self) -> str:
        def __parameters__() -> str:
            parameters: list[str] = []
            _kind: inspect._ParameterKind = inspect._ParameterKind.POSITIONAL_ONLY
            for name, param in self.signature.parameters.items():
                _parameter = (
                    name
                    + f': {param.annotation.__name__}' if param.annotation is not inspect.Parameter.empty else ''
                    + f' = {param.default}' if param.default is not inspect.Parameter.empty else ''
                )
                match param.kind:
                    case inspect._ParameterKind.POSITIONAL_OR_KEYWORD:
                        if _kind != param.kind:
                            _kind = param.kind
                            if len(parameters) > 0:
                                parameters.append('/')
                    case inspect._ParameterKind.VAR_POSITIONAL:
                        _kind = param.kind
                        _parameter = f'*{_parameter}'
                    case inspect._ParameterKind.KEYWORD_ONLY:
                        if _kind != param.kind:
                            if _kind != inspect._ParameterKind.VAR_POSITIONAL:
                                parameters.append('*')
                            _kind = param.kind
                    case inspect._ParameterKind.VAR_KEYWORD:
                        _parameter = f'**{_parameter}'
            
            return ', '.join(parameters)
        
        return (
            repr(self.call)
            + f'({__parameters__()})'
            + (
                f'-> {self.signature.return_annotation.__name__}'
                if self.signature.return_annotation is not inspect.Parameter.empty and self.signature.return_annotation is not None else
                '-> None' if self.signature.return_annotation is None else
                ''
            )
        )
    
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
    
    def cancel(self, force: bool = False) -> bool:
        '''取消任务'''
        if (_signal := getattr(self.thread, '__stop_signal', None)) is not None:
            if not _signal.is_set():
                _signal.set()
        if not force:
            return self.future.cancel()
        else:
            self.future.cancel()
            if self.thread:
                self.thread.join(0)
            return True

class ThreadPoolExecutor:
    '''总线程池执行器
    
    将会在多个单独的线程中执行任务，
    所有的任务都将受到该线程池管理。
    '''
    
    _worker_lock: Lock = Lock()
    _submit_block: bool = False
    _all_tasks: list[Task[Any]] = []
    
    def __init__(self, max_workers: Optional[int] = None) -> None:
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        self._tasks: Queue[Task[Any]] = Queue()
        self._workers: set[Thread] = set()
        self._main_thread: Optional[Thread] = None
        self._max_workers: int = max_workers
    
    def __repr__(self) -> str:
        return f'ThreadPoolExecutor(max_workers={self._max_workers})'
    
    def _run_workers(self) -> None:
        for _ in range(self._max_workers):
            thread = _Thread(target=self._worker, daemon=True)
            thread.start()
            self._workers.add(thread)
    
    @classmethod
    def run_executor(cls, max_workers: Optional[int] = None) -> 'ThreadPoolExecutor':
        executor = cls(max_workers)
        _thread = _Thread(target=executor._run_workers, daemon=True)
        _thread.start()
        executor._main_thread = _thread
        return executor
    
    def _worker(self) -> None:
        while True:
            task = self._tasks.get()
            try:
                task()
            except BaseException as exception:
                task.future.set_exception(exception)
            finally:
                if task in self._all_tasks:
                    self._all_tasks.remove(task)
    
    def _temp_worker(self, task: Task[Any]) -> None:
        try:
            task()
        except BaseException as exception:
            task.future.set_exception(exception)
        finally:
            if task in self._all_tasks:
                self._all_tasks.remove(task)

    def submit(self, task: Task[R], temp: bool = False) -> Future[R]:
        '''提交一个任务到线程池执行器'''
        if self._submit_block:
            raise RuntimeError('线程池执行器已关闭')
        with self._worker_lock:
            self._all_tasks.append(task)
            if temp:
                _thread = _Thread(target=self._temp_worker, args=(task,), daemon=True)
                _thread.start()
            else:
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

def gather(*sync_futures: Union[_SyncFutureLike[R], Task[R]], return_exceptions: bool=False) -> _FutureResults[R]:
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
                get_pool_executor().submit(sync_future, True)
            ] = index
        else:
            _futures[sync_future.future] = index
    for future in as_completed(_futures):
        try:
            result[_futures[future]] = future.result()
        except CancelledError:
            pass
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
    try:
        return task.future.result(timeout)
    except CancelledError:
        return

def create_task(task: Union[Callable[..., R], Task[R]], *args: Any, temp: bool = False, **kwargs: Any) -> Task[R]:
    '''创建并立刻运行一个任务'''
    if not isinstance(task, Task):
        task = Task[R](task, *args, **kwargs)
    get_pool_executor().submit(task, temp)
    return task

class CancelledError(BaseException):
    '''`Future` 或 `Task` 被取消，导致线程被中断。'''
    pass
