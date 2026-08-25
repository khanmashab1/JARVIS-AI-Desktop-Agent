"""Asynchronous helpers and thread pool runners."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")

_GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="jarvis-worker")


async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a blocking synchronous function in a thread pool without freezing the async loop."""
    loop = asyncio.get_running_loop()
    if kwargs:
        return await loop.run_in_executor(_GLOBAL_EXECUTOR, lambda: func(*args, **kwargs))
    return await loop.run_in_executor(_GLOBAL_EXECUTOR, func, *args)


async def with_timeout(coro: Coroutine[Any, Any, T], timeout_seconds: float, error_msg: str = "Operation timed out") -> T:
    """Execute a coroutine with a timeout threshold."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(error_msg)
