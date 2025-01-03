from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Sequence

import asyncpg
import discord
from discord.audit_logs import F
from discord.ext import commands
from discord.ext.commands import Converter

from ..utils import FakeRecord
from .embed import YEmbed

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..main import Yuno


__all__: tuple[str, ...] = ("YUser", "FuzzyMember")

logger = logging.getLogger(__name__)


class YUser:
    def __init__(self, record: asyncpg.Record | FakeRecord) -> None:
        self.user_id = record["user_id"]
        self.time_zone = record["time_zone"]
        self.locale = record["locale"]
        self.added_at = record["added_at"]

    @staticmethod
    async def upsert_user(
        db: asyncpg.Connection,
        user_id: int,
        time_zone: str = "UTC",
        locale: str = "en_US",
    ) -> YUser:
        record = await db.execute(
            """
            INSERT INTO users (user_id, time_zone, locale)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET time_zone = $2, locale = $3
            """,
            user_id,
            time_zone,
            locale,
        )
        return await YUser.get_user(db, user_id)  # type: ignore

    @staticmethod
    async def insert_many(
        db: asyncpg.Connection,
        users: Sequence[YUser],
    ) -> None:
        await db.executemany(
            """
            INSERT INTO users (user_id, time_zone, locale)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO NOTHING
            """,
            [(user.user_id, "UTC", "en_US") for user in users],
        )

    @staticmethod
    async def get_user(db: asyncpg.Connection, user_id: int) -> Optional[YUser]:
        record = await db.fetchrow(
            """
            SELECT * FROM users
            WHERE user_id = $1
            """,
            user_id,
        )
        return YUser(record) if record else None

    @staticmethod
    def settings_embed(ctx: Context, user: YUser) -> YEmbed:
        return YEmbed.default(
            ctx,
            title="User Settings",
            description=(f"**Time Zone:** {user.time_zone}\n" f"**Locale:** {user.locale}"),
        )

    @classmethod
    async def from_discord_user(cls, db: asyncpg.Connection, user: discord.User | discord.Member) -> YUser:
        return await cls.upsert_user(db, user.id)

    @classmethod
    async def get_user_language(cls, db: asyncpg.Connection, user: discord.User | discord.Member) -> str:
        record = await db.fetchrow(
            """
            SELECT locale FROM users
            WHERE user_id = $1
            """,
            user.id,
        )
        return record["locale"] if record else "en_US"

    @classmethod
    async def fake_user(cls, id: int) -> YUser:
        return cls(FakeRecord({"user_id": id, "time_zone": "UTC", "locale": "en_US", "added_at": None}))


class FuzzyMember(Converter):
    async def convert(self, ctx: Context[Yuno], argument: str) -> Optional[discord.Member]:
        assert ctx.guild is not None  # Check happens on command invocation (we don't do dm commands)

        if argument is None:
            return None

        try:
            member = await commands.MemberConverter().convert(ctx, argument)
        except commands.errors.MemberNotFound:
            members = await ctx.guild.query_members(argument, limit=1)
            member = members[0] if members else None

        return member
