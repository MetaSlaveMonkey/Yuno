from __future__ import annotations

import abc
import difflib
import functools
import itertools
from typing import (TYPE_CHECKING, Any, Callable, Concatenate, Dict, Generator,
                    Iterable, List, Mapping, NamedTuple, Optional, ParamSpec,
                    Self, Sequence, Tuple, Type, TypeAlias, TypeVar, Union)

import discord
from discord import SelectOption
from discord.ext import commands
from discord.ui import Button, Select, View
from discord.utils import get

from bot.classes.user import YUser

from ..classes import YEmbed

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..main import Yuno


T = TypeVar("T")
P = ParamSpec("P")


def patch_init(__init__: Callable[Concatenate["HelpView", P], T]) -> Callable[Concatenate["HelpView", P], T]:
    @functools.wraps(__init__)
    async def wrapper(self: HelpView, *args: P.args, **kwargs: P.kwargs) -> T:
        wrapped_ret = __init__(self, *args, **kwargs)
        await self.setup_view()
        return wrapped_ret

    return wrapper  # type: ignore


def grouper(n: int, iterable: Iterable[T]) -> Generator[Tuple[T, ...], None, None]:
    it = iter(iterable)
    while chunk := tuple(itertools.islice(it, n)):
        if not chunk:
            return
        yield chunk


def get_close_matches(word: str, possibilities: Sequence[str], n: int = 3, cutoff: float = 0.6) -> List[str]:
    return difflib.get_close_matches(word, possibilities, n, cutoff)


class HomeButton(Button["HelpView"]):
    def __init__(self, view: HelpView) -> None:
        super().__init__(style=discord.ButtonStyle.blurple, label="\N{HOUSE BUILDING}")
        self._view = view


class StopButton(Button["HelpView"]):
    def __init__(self, view: HelpView) -> None:
        super().__init__(style=discord.ButtonStyle.danger, label="\N{NO ENTRY}")
        self._view = view


class BackButton(Button["HelpView"]):
    def __init__(self, view: HelpView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="\N{LEFTWARDS ARROW WITH HOOK}")
        self._view = view


class HelpTranslator:
    def __init__(self, ctx: Context[Yuno], user: YUser) -> None:
        self.bot: Yuno = ctx.bot
        self._current_user = user

    def get_translation(self, key: str) -> str | dict[str, str]:
        return self.bot.translator.get_translation(key, self._current_user.locale)


class HelpView(View, abc.ABC):
    def __init_subclass__(cls) -> None:
        cls.__init__ = patch_init(cls.__init__)  # type: ignore
        return super().__init_subclass__()

    def __init__(self, ctx: Context[Yuno], user: YUser, timeout: int = 60, parent: HelpView | None = None) -> None:
        super().__init__(timeout=timeout)

        self.ctx = ctx
        self.user = user
        self.bot: Yuno = ctx.bot
        self.parent = parent

        self._translator = HelpTranslator(self.ctx, self.user)

    async def setup_view(self) -> None:
        if self.parent is not None:
            self.add_item(BackButton(self.parent))

            home = self.find_home(self)
            if home is not None:
                self.add_item(HomeButton(home))

        self.add_item(StopButton(self))

    @abc.abstractmethod
    def create_embed(self) -> YEmbed:
        raise NotImplementedError

    @staticmethod
    def find_home(view: Optional[HelpView]) -> Optional[HelpView]:
        home = view

        if parent := getattr(home, "parent", None):
            home = parent

        if home is view:
            return None

        return home

    async def interaction_check(self, interaction: discord.Interaction[discord.Client]) -> bool:
        check = self.ctx.author.id == interaction.user.id

        if not check:
            await interaction.response.send_message("You can't use this view.", ephemeral=True)

        return check

    async def _get_class_info(self) -> dict[str, Any]:
        return {
            "ctx": self.ctx,
            "user": self.user,
            "timeout": self.timeout,
            "parent": self.parent,
        }
