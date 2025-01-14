from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Sequence

import asyncpg
import discord

if TYPE_CHECKING:
    from datetime import datetime

    from discord.ext.commands import Context

    from ..main import Yuno


__all__: tuple[str, ...] = ("YGuild",)


class YGuild:
    def __init__(self, record: asyncpg.Record) -> None:
        self.guild_id: int = record["guild_id"]
        self.locale: str = record["locale"]
        self.added_at: datetime = record["added_at"]

    @staticmethod
    async def upsert_guild(db: asyncpg.Connection, guild_id: int, locale: str = "en_US") -> YGuild:
        await db.execute(
            """
            INSERT INTO guilds (guild_id, locale, added_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id)
            DO UPDATE SET locale = $2
            """,
            guild_id,
            locale,
            discord.utils.utcnow(),
        )
        return await YGuild.get_guild(db, guild_id)  # type: ignore

    @staticmethod
    async def insert_many(
        db: asyncpg.Connection,
        guilds: Sequence[YGuild],
    ) -> None:
        await db.executemany(
            """
            INSERT INTO guilds (guild_id, locale)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id)
            DO NOTHING
            """,
            [(guild.guild_id, "en_US", discord.utils.utcnow()) for guild in guilds],
        )

    @staticmethod
    async def get_guild(db: asyncpg.Connection, guild_id: int) -> Optional[YGuild]:
        record = await db.fetchrow("SELECT * FROM guilds WHERE guild_id = $1", guild_id)

        return YGuild(record) if record else None

    @staticmethod
    async def get_all_guilds(db: asyncpg.Connection) -> List[YGuild]:
        records = await db.fetch("SELECT * FROM guilds")

        return [YGuild(record) for record in records]

    @staticmethod
    async def get_locale(db: asyncpg.Connection, guild_id: int) -> str:
        record = await db.fetchval("SELECT locale FROM guilds WHERE guild_id = $1", guild_id)

        return record or "en_US"
