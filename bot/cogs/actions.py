from __future__ import annotations

import difflib
import aiohttp
import logging

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, cast, Any

import asyncpg
import discord
from discord.ext import commands, tasks

from ..classes import YEmbed, YUser, UserInteractions, FuzzyMember
from ..utils import module_ruleset

if TYPE_CHECKING:
    from ..main import Yuno
    from discord.ext.commands import Context

log = logging.getLogger(__name__)


FuzzyConverter = commands.parameter(converter=FuzzyMember, default=None)


__all__: tuple[str, ...] = (
    "UserInteractionModule",
)


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

        if not ctx.author in bot.cached_users:
            async with bot.pool.acquire() as conn:
                bot.cached_users[ctx.author.id] = await YUser.from_discord_user(conn, ctx.author)
        
        return True
    
    async def get_user_language(self, user_id: int) -> str:
        if user_id in self.bot.cached_users:
            return self.bot.cached_users[user_id].locale
        
        if self.bot.pool is None:
            return "en_US"

        async with self.bot.pool.acquire() as conn:
            record = await conn.fetchrow("SELECT locale FROM users WHERE user_id = $1", user_id)
            return record['locale'] if record else 'en_US'

    async def get_guild_language(self, guild_id: int) -> str:
        if guild_id in self.bot.cached_guilds:
            return self.bot.cached_guilds[guild_id].locale
        
        if self.bot.pool is None:
            return "en_US"
        
        async with self.bot.pool.acquire() as conn:
            record = await conn.fetchrow("SELECT locale FROM guilds WHERE guild_id = $1", guild_id)
            return record['locale'] if record else 'en_US'

    async def _get_interaction_count(self, author: YUser, target: YUser, action: str) -> int:
        if self.bot.pool is None:
            log.warning("No pool available.")
            return 0

        async with self.bot.pool.acquire() as conn:
            count = await self.interactions.get_action_count(
                conn,
                author.user_id,
                target.user_id,
                action
            )

        return count or 0
    
    async def _get_interactions(self, author: YUser, target: YUser) -> List[str]:
        if self.bot.pool is None:
            log.warning("No pool available.")
            return []

        async with self.bot.pool.acquire() as conn:
            actions = await self.interactions.get_actions(
                conn,
                author.user_id,
                target.user_id
            )

        return actions
    
    async def _get_embed(
            self,
            pool: asyncpg.Pool,
            author: discord.Member | discord.User,
            target: discord.Member | discord.User,
            interaction_name: str,
            author_lang: str
        ) -> YEmbed:
        if self.bot.pool is None:
            log.warning("No pool available.")
            raise ValueError("No pool available.")

        return await self.interactions.get_embed(
            pool,
            author,
            target,
            interaction_name,
            author_lang
        )
    
    async def insert_action(self, pool: asyncpg.Pool, author_id: int, target_id: int, action: str) -> None:
        async with pool.acquire() as conn:
            await conn.execute(
                "SELECT insert_action_item($1, $2, $3)",
                author_id,
                target_id,
                action
            )
    
    @commands.command(
        name="hug",
        aliases=[],
        description="Hug someone you love.",
        usage="hug <user>",
    )
    async def hug(
        self,
        ctx: Context,
        target: discord.Member = FuzzyConverter
    ) -> None:
        if self.bot.pool is None:
            return log.warning("No pool available.")
        
        if target is None:
            user_lang = await self.get_user_language(ctx.author.id)
            message = self.bot.localise('errors.no_user', locale=user_lang)
            return await ctx.send(message)
        
        await self.insert_action(self.bot.pool, ctx.author.id, target.id, "hug")
        
        #embed = await self._get_embed(ctx.author, target, "hug")
        #author_lang = await self.get_user_language(ctx.author.id)
        if ctx.author.id in self.bot.cached_users:
            author_lang = self.bot.cached_users[ctx.author.id].locale
        else:
            user = await YUser.upsert_user(self.bot.pool, ctx.author.id)  # type: ignore
            author_lang = user.locale
            self.bot.cached_users[ctx.author.id] = user

        ...  # Finish the command


        #await ctx.send(embed=embed)



async def setup(bot: Yuno) -> None:
    await bot.add_cog(UserInteractionModule(bot))
    log.info("Cog loaded: UserInteractionModule")
