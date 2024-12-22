from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

from discord import Color, Embed, utils

if TYPE_CHECKING:
    from discord.ext.commands import Context

from ..config import Config

conf = Config()


__all__ = ("YEmbed",)


class YEmbed(Embed):
    @classmethod
    def default(cls, ctx: Context, **kwargs: Any) -> YEmbed:
        embed = cls(timestamp=utils.utcnow(), **kwargs)
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url
        )
        return embed

    @classmethod
    def action_command(
        cls,
        gif: Optional[str] = None,
        description: Optional[str] = None,
        footer: Optional[str] = None,
        color: Optional[Union[int, Color]] = conf.DEFAULT_COLOR,
        **kwargs: Any,
    ) -> YEmbed:
        embed = cls(description=description, color=color, **kwargs)
        embed.set_image(url=gif)
        embed.set_footer(text=footer)
        return embed

    @classmethod
    def error(
        cls,
        title: str,
        description: Optional[str] = None,
        footer: Optional[str] = None,
        color: Optional[Union[int, Color]] = Color.red(),
        **kwargs: Any,
    ) -> YEmbed:
        embed = cls(title=title, description=description, color=color, **kwargs)
        embed.set_footer(text=footer)
        return embed

    @classmethod
    def success(
        cls,
        title: str,
        description: Optional[str] = None,
        footer: Optional[str] = None,
        color: Optional[Union[int, Color]] = Color.green(),
        **kwargs: Any,
    ) -> YEmbed:
        embed = cls(title=title, description=description, color=color, **kwargs)
        embed.set_footer(text=footer)
        return embed
