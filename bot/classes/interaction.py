from __future__ import annotations

import random
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import asyncpg
import discord
import orjson

from ..config import Config
from .embed import YEmbed

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..main import Yuno


conf = Config()

__all__: tuple[str, ...] = ("UserInteractions",)


class UserInteractions:
    async def get_embed(
        self,
        ctx: Context[Yuno],
        author: discord.Member | discord.User,
        target: discord.Member | discord.User,
        count: int,
        footer: str,
        description: str,
        emoji: Optional[str] = None,
    ) -> YEmbed:
        embed = YEmbed.default(
            ctx,
            description=(
                f"{emoji}" if emoji else "" + description.format(author=author.display_name, target=target.display_name)
            ),
            footer=footer.format(
                author=author.display_name,
                target=target.display_name,
                count=count,
            ),
        )

        return embed

    async def insert_action(self, db: asyncpg.Pool, author_id: int, target_id: int, action: str) -> None:
        await db.execute("SELECT insert_action_item($1, $2, $3)", author_id, target_id, action)

    async def get_actions(self, db: asyncpg.Pool, author_id: int, target_id: int) -> list[str]:
        return await db.fetch(
            "SELECT action_type FROM action WHERE user_id = $1 AND target_id = $2 ORDER BY action_count DESC",
            author_id,
            target_id,
        )

    async def get_action_count(self, db: asyncpg.Pool, author_id: int, target_id: int, action: str) -> int:
        record = await db.fetchval(
            "SELECT action_count FROM action WHERE user_id = $1 AND target_id = $2 AND action_type = $3",
            author_id,
            target_id,
            action,
        )

        return record or 0
