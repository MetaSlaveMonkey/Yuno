from __future__ import annotations

import random
from itertools import count
from pathlib import Path
from typing import Any

import asyncpg
import discord
import orjson

from .embed import YEmbed

__all__ = ("UserInteractions",)


class UserInteractions:
    GOOD = orjson.loads((Path(__file__).parent / "data" / "good_int.json").read_text(encoding="utf-8"))
    BAD = orjson.loads((Path(__file__).parent / "data" / "bad_int.json").read_text(encoding="utf-8"))

    async def get_embed(
        self,
        connection: asyncpg.Pool,
        author: discord.Member | discord.User,
        target: discord.Member | discord.User,
        interaction_name: str,
        lang: str,
    ) -> YEmbed: ...  # TODO: add translation logic

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
