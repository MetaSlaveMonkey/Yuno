from __future__ import annotations

from itertools import count
import random

from pathlib import Path
from typing import Any

import orjson
import asyncpg
import discord

from .embed import YEmbed


__all__ = (
    "UserInteractions",
)


class UserInteractions:
    GOOD = orjson.loads((Path(__file__).parent / "data" / "good_int.json").read_text(encoding="utf-8"))
    BAD = orjson.loads((Path(__file__).parent / "data" / "bad_int.json").read_text(encoding="utf-8"))

    @classmethod
    def get_interaction(cls, interaction_name: str) -> dict[str, Any] | None:
        return cls.GOOD.get(interaction_name) or cls.BAD.get(interaction_name)
    
    async def get_embed(
            self,
            connection: asyncpg.Connection,
            author: discord.Member | discord.User,
            target: discord.Member | discord.User,
            interaction_name: str
        ) -> YEmbed:
        interaction = self.get_interaction(interaction_name)
        
        if interaction is None:
            raise ValueError(f"Interaction {interaction_name} not found.")
        
        count = await self.get_action_count(connection, author.id, target.id, interaction_name)

        embed = YEmbed.action_command(
            description=interaction["text"],
            gif=random.choice(interaction["gifs"]),
            color=interaction["color"] if interaction["color"] else None
        )

        footer_message = interaction["message"].format(
            author=author.display_name,
            target=target.display_name,
            count=count
        )

        embed.set_footer(text=footer_message)

        return embed
    
    async def insert_action(self, db: asyncpg.Connection, author_id: int, target_id: int, action: str) -> None:
        await db.execute(
            "SELECT insert_action_item($1, $2, $3)",
            author_id,
            target_id,
            action
        )

    async def get_actions(self, db: asyncpg.Connection, author_id: int, target_id: int) -> list[str]:
        return await db.fetch(
            "SELECT action_type FROM action WHERE user_id = $1 AND target_id = $2 ORDER BY action_count DESC",
            author_id,
            target_id
        )
    
    async def get_action_count(self, db: asyncpg.Connection, author_id: int, target_id: int, action: str) -> int:
        record = await db.fetchval(
            "SELECT action_count FROM action WHERE user_id = $1 AND target_id = $2 AND action_type = $3",
            author_id,
            target_id,
            action
        )

        return record or 0
