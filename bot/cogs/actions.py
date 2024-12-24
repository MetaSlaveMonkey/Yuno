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


@module_ruleset(commands.cooldown(rate=1, per=5, type=commands.BucketType.user))
class UserInteractionModule(commands.Cog, name="User Interactions"):
    def __init__(self, bot: Yuno) -> None:
        self.bot = bot
        self.interactions = UserInteractions()

    async def cog_check(self, ctx: Context[Yuno]) -> bool:  # type: ignore
        if ctx.guild is None:
            raise commands.NoPrivateMessage(":x: | This command is not available in DMs.")

        bot = cast(Yuno, ctx.bot)
        assert bot.pool is not None, "No pool available."

        if ctx.author.id not in bot.OWNER_IDS:
            return True

        if ctx.author.id not in bot.user_cache._cache:
            async with bot.pool.acquire() as conn:
                user = await bot.user_cache.get_user(conn, ctx.author.id)
                await bot.user_cache.set_user(user)

        return True

    async def insert_action(self, pool: asyncpg.Pool, author_id: int, target_id: int, action: str) -> None:
        async with pool.acquire() as conn:
            await conn.execute("SELECT insert_action_item($1, $2, $3)", author_id, target_id, action)


async def setup(bot: Yuno) -> None:
    await bot.add_cog(UserInteractionModule(bot))
    log.info("Cog loaded: UserInteractionModule")
