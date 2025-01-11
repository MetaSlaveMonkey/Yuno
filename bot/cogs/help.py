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


class HelpView(View, abc.ABC):
    def __init_subclass__(cls) -> None:
        cls.__init__ = patch_init(cls.__init__)  # type: ignore
        return super().__init_subclass__()

    def __init__(
        self,
        ctx: Context[Yuno],
        user: YUser,
        parent: Optional[HelpView] = None,
        timeout: float = 180.0
    ) -> None:
        super().__init__(timeout=timeout)

        self.ctx = ctx
        self.user = user
        self.bot: Yuno = ctx.bot
        self.parent = parent
        self._translator = HelpTranslator(self.ctx, self.user)

    async def setup_view(self) -> None:
        if self.parent is not None:
            self.add_item(BackButton(self.parent))

            root = self.find_root_view(self)
            if root is not None:
                self.add_item(HomeButton(root))

        self.add_item(StopButton(self))

    @abc.abstractmethod
    def to_embed(self) -> YEmbed:
        raise NotImplementedError

    @staticmethod
    def find_root_view(view: Optional[HelpView]) -> Optional[HelpView]:
        root_view = view
        if parent_view := getattr(root_view, "parent", None):
            root_view = parent_view

        if root_view is view:
            return None
        
        return root_view

    async def interaction_check(self, interaction: discord.Interaction[discord.Client]) -> bool:
        check = self.ctx.author.id == interaction.user.id

        if not check:
            await interaction.response.send_message("You can't interact with this view.", ephemeral=True)

        return check

    async def _get_class_info(self) -> dict[str, Any]:
        return {
            "ctx": self.ctx,
            "user": self.user,
            "timeout": self.timeout,
            "parent": self.parent,
        }


class HomeButton(Button["HelpView"]):
    def __init__(self, view: HelpView) -> None:
        super().__init__(
            emoji="\N{HOUSE BUILDING}",
            label="Home",
            style=discord.ButtonStyle.primary
        )
        self.bot: Yuno = view.bot
        self.parent = view.parent

    async def callback(self, interaction: discord.Interaction[Yuno]) -> None:
        return await interaction.response.edit_message(view=self.parent, embed=self.parent.to_embed())  # type: ignore

class StopButton(Button["HelpView"]):
    def __init__(self, view: HelpView) -> None:
        super().__init__(style=discord.ButtonStyle.danger, label="\N{NO ENTRY}")
        self.parent = view

    async def callback(self, interaction: discord.Interaction[Yuno]) -> None:
        for child in self.parent.children:
            setattr(child, "disabled", True)

        self.parent.stop()
        return await interaction.response.edit_message(view=self.parent)

class BackButton(Button["HelpView"]):
    def __init__(self, view: HelpView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="\N{LEFTWARDS ARROW WITH HOOK}")
        self.parent = view.parent

    async def callback(self, interaction: discord.Interaction[Yuno]) -> None:
        return await interaction.response.edit_message(embed=self.parent.embed, view=self.parent)  # type: ignore


class HelpTranslator:
    def __init__(self, ctx: Context[Yuno], user: YUser) -> None:
        self.bot: Yuno = ctx.bot
        self._current_user = user

    def get_translation(self, key: str) -> str | dict[str, str]:
        return self.bot.translator.get_translation(key, self._current_user.locale)
