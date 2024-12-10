from __future__ import annotations

import asyncio
import functools

from concurrent.futures import ThreadPoolExecutor
from typing import (
    Awaitable,
    Callable,
    ParamSpec,
    TypeVar,
    Type,
    Any,
)

from discord.app_commands import Command as AppCommand
from discord.ext.commands import Command as ExtCommand


T = TypeVar("T")
P = ParamSpec("P")
executor = ThreadPoolExecutor()

__all__: tuple[str, ...] = (
    "run_async",
    "module_ruleset",
)


def module_ruleset(decorator: Callable[[T], T]) -> Callable[[Type[T]], Type[T]]:
    def decorate(cls: Type[T]) -> Type[T]:
        for attr_name in cls.__dict__:
            attr = getattr(cls, attr_name)
            if isinstance(attr, (AppCommand, ExtCommand)):
                setattr(cls, attr_name, decorator(attr))  # type: ignore

        return cls
    
    return decorate


def run_async(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return await asyncio.get_event_loop().run_in_executor(executor, functools.partial(func, *args, **kwargs))

    return wrapper
