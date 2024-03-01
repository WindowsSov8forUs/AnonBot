from typing import Any, Callable, TypeAlias

LIFESPAN_FUNC: TypeAlias = Callable[[], Any]

class Lifespan:
    def __init__(self) -> None:
        self._startup_funcs: list[LIFESPAN_FUNC] = []
        self._shutdown_funcs: list[LIFESPAN_FUNC] = []
    
    def on_startup(self, func: LIFESPAN_FUNC) -> LIFESPAN_FUNC:
        self._startup_funcs.append(func)
        return func
    
    def on_shutdown(self, func: LIFESPAN_FUNC) -> LIFESPAN_FUNC:
        self._shutdown_funcs.append(func)
        return func
    
    @staticmethod
    def _run_func(funcs: list[LIFESPAN_FUNC]) -> None:
        for func in funcs:
            func()
    
    def startup(self) -> None:
        if self._startup_funcs:
            self._run_func(self._startup_funcs)
    
    def shutdown(self) -> None:
        if self._shutdown_funcs:
            self._run_func(self._shutdown_funcs)
    
    def __enter__(self) -> None:
        self.startup()
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()