from __future__ import annotations

from typing import Sequence, List, TYPE_CHECKING, Optional

import asyncpg
import discord

if TYPE_CHECKING:
    from ..main import Yuno
    from discord.ext.commands import Context


__all__: tuple[str, ...] = (
    "YGuild",
)


class YGuild:
    def __init__(self, record: asyncpg.Record) -> None:
        self.guild_id = record['guild_id']
        self.locale = record['locale']
        self.added_at = record['added_at']

    @staticmethod
    async def upsert_guild(
        db: asyncpg.Connection,
        guild_id: int,
        locale: str = "en_US"
    ) -> YGuild:
        await db.execute(
            """
            INSERT INTO guilds (guild_id, prefix, locale)
            VALUES ($1, $2)
            ON CONFLICT (guild_id)
            DO UPDATE SET locale = $2
            """,
            guild_id,
            locale
        )
        return await YGuild.get_guild(db, guild_id)  # type: ignore
    
    @staticmethod
    async def insert_many(
        db: asyncpg.Connection,
        guilds: Sequence[YGuild],
    ) -> None:
        await db.executemany(
            """
            INSERT INTO guilds (guild_id, prefix, locale)
            VALUES ($1, $2)
            ON CONFLICT (guild_id)
            DO NOTHING
            """,
            [(guild.guild_id, "en_US") for guild in guilds]
        )

    @staticmethod
    async def get_guild(
        db: asyncpg.Connection,
        guild_id: int
    ) -> Optional[YGuild]:
        record = await db.fetchrow(
            "SELECT * FROM guilds WHERE guild_id = $1",
            guild_id
        )

        return YGuild(record) if record else None
    
    @staticmethod
    async def get_all_guilds(
        db: asyncpg.Connection
    ) -> List[YGuild]:
        records = await db.fetch("SELECT * FROM guilds")

        return [YGuild(record) for record in records]
    
    @staticmethod
    async def get_locale(
        db: asyncpg.Connection,
        guild_id: int
    ) -> str:
        record = await db.fetchval(
            "SELECT locale FROM guilds WHERE guild_id = $1",
            guild_id
        )

        return record or "en_US"
    
    @staticmethod
    async def get_prefix(
        db: asyncpg.Connection,
        guild_id: int
    ) -> list[str]:
        records = await db.fetch("SELECT prefix FROM guilds WHERE guild_id = $1", guild_id)
        return [record['prefix'] for record in records] if records else ["y"]
    
    @staticmethod
    async def update_prefix(
        db: asyncpg.Connection,
        guild_id: int,
        prefix: str
    ) -> None:
        await db.execute(
            "UPDATE guilds SET prefix = $1 WHERE guild_id = $2",
            prefix,
            guild_id
        )
