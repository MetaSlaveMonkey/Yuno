from __future__ import annotations

import difflib
import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional, cast

import aiohttp
import asyncpg
import discord
from discord.ext import commands, tasks

from ..classes import FuzzyMember, UserInteractions, YEmbed, YUser
from ..utils import module_ruleset

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from ..main import Yuno

log = logging.getLogger(__name__)


FuzzyMemberConverter = commands.parameter(converter=FuzzyMember, default=None)


__all__: tuple[str, ...] = ("UserInteractionModule",)


class Interaction:
    int_type: str
    author: YUser
    target: YUser


@module_ruleset(commands.guild_only())
@module_ruleset(commands.cooldown(rate=1, per=5, type=commands.BucketType.user))
class UserInteractionModule(commands.Cog, name="User Interactions"):
    def __init__(self, bot: Yuno) -> None:
        self.bot = bot
        self.interactions = UserInteractions()

    async def cog_check(self, ctx: Context[Yuno]) -> bool:  # type: ignore (idk man)
        if ctx.guild is None:
            raise commands.NoPrivateMessage(".-.")

        bot = cast(Yuno, ctx.bot)

        if ctx.author.id not in bot.OWNER_IDS:
            return True

        if ctx.author.id not in await bot.user_cache.get_users():
            async with bot.pool.acquire() as conn:
                user = await bot.user_cache.fetch_user(conn, ctx.author.id)
                await bot.user_cache.set_user(user)

        return True

    async def ensure_relationship(self, interaction: Interaction) -> None:
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "SELECT ensure_relationship($1, $2, $3)",
                interaction.author.user_id,
                interaction.int_type,
                interaction.target.user_id,
            )

    async def insert_action(self, interaction: Interaction) -> None:
        await self.ensure_relationship(interaction)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "SELECT insert_action($1, $2, $3)",
                interaction.author.user_id,
                interaction.int_type,
                interaction.target.user_id,
            )

    async def get_count(self, interaction: Interaction) -> int:
        async with self.bot.pool.acquire() as conn:
            record = await conn.fetchval(
                """
                SELECT action_count FROM actions
                WHERE user_id = $1 
                AND target_id = $2
                AND action_type = $3
                """,
                interaction.author.user_id,
                interaction.target.user_id,
                interaction.int_type,
            )

            return record["action_count"] if record else 0

    async def get_total_count(self, interaction: Interaction) -> int:
        async with self.bot.pool.acquire() as conn:
            record = await conn.fetchval(
                """
                SELECT SUM(action_count) FROM actions
                WHERE user_id = $1 
                AND target_id = $2
                AND action_type = $3
                """,
                interaction.author.user_id,
                interaction.target.user_id,
                interaction.int_type,
            )

            return record["action_count"] if record else 0


async def setup(bot: Yuno) -> None:
    await bot.add_cog(UserInteractionModule(bot))
    log.info("Cog loaded: UserInteractionModule")
