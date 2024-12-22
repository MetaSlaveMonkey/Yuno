from __future__ import annotations

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import (TYPE_CHECKING, Any, AsyncIterator, Awaitable, Callable,
                    Iterable, Iterator, Optional, ParamSpec, Type, TypeVar,
                    overload)

import discord
from discord.app_commands import Command as AppCommand
from discord.ext.commands import Command as ExtCommand

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..classes import YEmbed
    from ..main import Yuno


T = TypeVar("T")
_T = TypeVar("_T")
P = ParamSpec("P")
executor = ThreadPoolExecutor()

__all__: tuple[str, ...] = (
    "run_async",
    "module_ruleset",
    "MessagePreview",
)


def module_ruleset(decorator: Callable[[T], T]) -> Callable[[Type[T]], Type[T]]:
    """A decorator for applying a decorator to all commands in a module

    Parameters
    ----------
    decorator : Callable[[T], T]
        The decorator to apply to the commands

    Returns
    -------
    Callable[[Type[T]], Type[T]]
        The decorated class
    """

    def decorate(cls: Type[T]) -> Type[T]:
        for attr_name in cls.__dict__:
            attr = getattr(cls, attr_name)
            if isinstance(attr, (AppCommand, ExtCommand)):
                setattr(cls, attr_name, decorator(attr))  # type: ignore
                # ^ idk how to type this -> its working tho so i guess its fine

        return cls

    return decorate


def run_async(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
    """Run a synchronous function in an asynchronous context

    Parameters
    ----------
    func : Callable[P, T]
        The function to run asynchronously

    Returns
    -------
    Callable[P, Awaitable[T]]
        The asynchronous function
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return await asyncio.get_event_loop().run_in_executor(
            executor, functools.partial(func, *args, **kwargs)
        )

    return wrapper


class MessagePreview:
    """A context manager for sending a temporary message with an embed

    Parameters
    ----------
    ctx : Context[Yuno]
        The context of the command
    content : str
        The content of the message
    embed : Optional[YEmbed], optional
        The embed to send, by default None
    """

    def __init__(
        self, ctx: Context[Yuno], content: str, embed: Optional[YEmbed] = None
    ) -> None:
        self.ctx = ctx
        self.embed = embed
        self.content = content
        self.message: Optional[discord.Message] = None

    async def __aenter__(self) -> None:
        if self.embed is None:
            self.message = await self.ctx.reply(content=self.content)
        else:
            self.message = await self.ctx.reply(content=self.content, embed=self.embed)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.message is not None:
            await self.message.delete()


class FakeRecord:
    def __init__(self, data: Optional[dict[str, Any]] = None) -> None:
        self._data: dict[str, Any] = data if data is not None else {}

    @overload
    def get(self, key: str) -> Any | None: ...

    @overload
    def get(self, key: str, default: _T) -> Any | _T: ...

    def get(self, key: str, default: Any | None = None) -> Any | None:
        return self._data.get(key, default)

    def items(self) -> Iterator[tuple[str, Any]]:
        return iter(self._data.items())

    def keys(self) -> Iterable[str]:
        return self._data.keys()

    def values(self) -> Iterable[Any]:
        return self._data.values()

    def __getitem__(self, index: str | int | slice) -> Any:
        if isinstance(index, str):
            return self._data[index]
        elif isinstance(index, int):
            return list(self._data.values())[index]
        elif isinstance(index, slice):
            return tuple(list(self._data.values())[index])
        else:
            raise TypeError(f"Invalid index type: {type(index)}")
