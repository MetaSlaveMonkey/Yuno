from __future__ import annotations

import asyncio
import datetime
import functools
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterable,
    Iterator,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    overload,
)

import asyncpg
import discord
from discord.app_commands import Command as AppCommand
from discord.ext.commands import Command as ExtCommand

from ..classes import YUser

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..classes import YEmbed
    from ..main import Yuno


T = TypeVar("T")
_T = TypeVar("_T")
P = ParamSpec("P")
executor = ThreadPoolExecutor()

__all__: tuple[str, ...] = (
    "async_try_catch",
    "run_async",
    "module_ruleset",
    "MessagePreview",
    "FakeRecord",
    "AsyncUserCache",
    "format_dt",
    "CaseInsensitiveDict",
)


async def async_try_catch(func: Callable[..., T], *args, catch=Exception, ret=False, **kwargs):
    try:
        return await discord.utils.maybe_coroutine(func, *args, **kwargs)
    except catch as e:
        return e if ret else None


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
        return await asyncio.to_thread(func, *args, **kwargs)

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

    def __init__(self, ctx: Context[Yuno], content: str, embed: Optional[YEmbed] = None) -> None:
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
        
class AsyncUserCache:
    def __init__(self) -> None:
        self._cache: dict[int, YUser] = {}
        self._lock = asyncio.Lock()

    async def set_user(self, user: YUser) -> None:
        async with self._lock:
            self._cache[user.user_id] = user

    async def get_users(self) -> list[YUser]:
        async with self._lock:
            return list(self._cache.values())

    async def fetch_user(self, db: asyncpg.Connection, user_id: int) -> YUser:
        async with self._lock:
            if user_id not in self._cache:
                await self.upsert_user(db, user_id)

            return self._cache[user_id]
        
    async def get_user(self, user_id: int) -> Optional[YUser]:
        async with self._lock:
            return self._cache.get(user_id)

    async def upsert_user(self, db: asyncpg.Connection, user_id: int) -> YUser:
        async with self._lock:
            user = await YUser.upsert_user(db, user_id)

            self._cache[user_id] = user

            return user

    async def insert_many(self, db: asyncpg.Connection, users: list[YUser]) -> None:
        async with self._lock:
            await YUser.insert_many(db, users)

            for user in users:
                self._cache[user.user_id] = user


def format_dt(dt: datetime.datetime, style: Optional[str] = None) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    if style is None:
        return f'<t:{int(dt.timestamp())}>'
    return f'<t:{int(dt.timestamp())}:{style}>'


class CaseInsensitiveDict(dict):
    def __contains__(self, k):
        return super().__contains__(k.casefold())

    def __delitem__(self, k):
        return super().__delitem__(k.casefold())

    def __getitem__(self, k):
        return super().__getitem__(k.casefold())

    def get(self, k, default=None):
        return super().get(k.casefold(), default)

    def pop(self, k, default=None):
        return super().pop(k.casefold(), default)

    def __setitem__(self, k, v):
        super().__setitem__(k.casefold(), v)
