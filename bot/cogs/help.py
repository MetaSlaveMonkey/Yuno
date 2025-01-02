from __future__ import annotations

import itertools
import difflib
import functools
import abc
from typing import (
    TYPE_CHECKING,
    Generator,
    Iterable,
    Sequence,
    Union,
    Dict,
    Mapping,
    List,
    Any,
    TypeVar,
    ParamSpec,
    Concatenate,
    NamedTuple,
    Self,
    TypeAlias,
    Callable,
    Type,
    Optional,
    Tuple,
)


import discord
from discord.ext import commands
from discord.ui import View, Button, Select

from bot.classes.user import YUser

from ..classes import YEmbed

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..main import Yuno


T = TypeVar("T")
P = ParamSpec("P")

CommandType: TypeAlias = commands.Command[Any, ..., Any]
CommandGroupType: TypeAlias = commands.Group[Any, ..., Any]

HOME_EMOJI = "\N{HOUSE BUILDING}"
STOP_LABEL = "Stop"
GO_HOME_LABEL = "Go Home"
GO_BACK_LABEL = "Go Back"


def grouper(n: int, iterable: Iterable[T]) -> Generator[Tuple[T, ...], None, None]:
    it = iter(iterable)
    while chunk := tuple(itertools.islice(it, n)):
        if not chunk:
            return
        yield chunk


def get_close_matches(word: str, possibilities: Sequence[str], n: int = 3, cutoff: float = 0.6) -> List[str]:
    return difflib.get_close_matches(word, possibilities, n, cutoff)


async def fetch_user(ctx: Context, user_id: int) -> YUser:
    async with ctx.bot.pool.acquire() as conn:
        user = await ctx.bot.user_cache.fetch_user(conn, user_id)
        await ctx.bot.user_cache.set_user(user)
    return user



class HelpTranslator:
    def __init__(self, ctx: Context[Yuno]) -> None:
        self.ctx = ctx
        self.bot: Yuno = ctx.bot

        self._current_user: YUser

    async def __aenter__(self) -> HelpTranslator:
        await self._ainit()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._aexit()

    async def _ainit(self) -> None:
        user = await self.bot.user_cache.get_user(self.ctx.author.id)

        if user is None:
            user = await fetch_user(self.ctx, self.ctx.author.id)

        self._current_user = user

    async def _aexit(self) -> None:
        await self.bot.user_cache.set_user(self._current_user)

    def get_translation(self, key: str) -> str:
        return self.bot.translator.get_translation(key, locale=self._current_user.locale)