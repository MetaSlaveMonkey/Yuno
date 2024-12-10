from __future__ import annotations

import difflib
import aiohttp
import logging

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, cast, Any

import discord
from discord.ext import commands, tasks

from ..classes import YEmbed, YUser, UserInteractions, FuzzyMember
from ..utils import module_ruleset

if TYPE_CHECKING:
    from ..main import Yuno
    from discord.ext.commands import Context

log = logging.getLogger(__name__)


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

    async def _increment_interaction_count(
            self,
            author: YUser,
            target: YUser,
            action: str
        ) -> None:
        if author == target:
            return
        
        if self.bot.pool is None:
            return log.warning("No pool available.")
            
        conn = await self.bot.pool.acquire()
        try:
            await self.interactions.insert_action(
                conn,
                author.user_id,
                target.user_id,
                action
            )
        finally:
            await self.bot.pool.release(conn)

    async def _get_interaction_count(self, author: YUser, target: YUser, action: str) -> int:
        if self.bot.pool is None:
            log.warning("No pool available.")
            return 0

        conn = await self.bot.pool.acquire()
        try:
            count = await self.interactions.get_action_count(
                conn,
                author.user_id,
                target.user_id,
                action
            )
        finally:
            await self.bot.pool.release(conn)

        return count or 0
    
    async def _get_interactions(self, author: YUser, target: YUser) -> List[str]:
        if self.bot.pool is None:
            log.warning("No pool available.")
            return []

        conn = await self.bot.pool.acquire()
        try:
            actions = await self.interactions.get_actions(
                conn,
                author.user_id,
                target.user_id
            )
        finally:
            await self.bot.pool.release(conn)

        return actions
    
    async def _get_embed(
            self,
            author: discord.Member | discord.User,
            target: discord.Member | discord.User,
            interaction_name: str
        ) -> YEmbed:
        if self.bot.pool is None:
            log.warning("No pool available.")
            raise ValueError("No pool available.")

        conn = await self.bot.pool.acquire()
        try:
            embed = await self.interactions.get_embed(
                conn,
                author,
                target,
                interaction_name
            )
        finally:
            await self.bot.pool.release(conn)

        return embed
    
    @commands.command(
        name="hug",
        aliases=[],
        description="Hug someone you love.",
        usage="hug <user>",
    )
    async def hug(
        self,
        ctx: Context,
        target: discord.Member = commands.parameter(converter=FuzzyMember, default=None)
    ) -> None:
        if self.bot.pool is None:
            return log.warning("No pool available.")
        
        if target is None:
            return await ctx.send("❌ | Please provide a user to hug.")
        
        conn = await self.bot.pool.acquire()

        await self._increment_interaction_count(
            await YUser.from_discord_user(conn, ctx.author),
            await YUser.from_discord_user(conn, target),
            "hug"
        )
        
        embed = await self._get_embed(ctx.author, target, "hug")

        await self.bot.pool.release(conn)
        await ctx.send(embed=embed)
    
    @commands.command(
        name="kiss",
        aliases=[],
        description="Kiss someone you love.",
        usage="kiss <user>",
    )
    async def kiss(
        self,
        ctx: Context,
        target: discord.Member = commands.parameter(converter=FuzzyMember, default=None)
    ) -> None:
        if self.bot.pool is None:
            return log.warning("No pool available.")
        
        if target is None:
            return await ctx.send("❌ | Please provide a user to kiss.")
        
        conn = await self.bot.pool.acquire()

        await self._increment_interaction_count(
            await YUser.from_discord_user(conn, ctx.author),
            await YUser.from_discord_user(conn, target),
            "kiss"
        )
        
        embed = await self._get_embed(ctx.author, target, "kiss")

        await self.bot.pool.release(conn)
        await ctx.send(embed=embed)

    @commands.command(
        name="bite",
        aliases=["nom"],
        description="Are you a vampire?",
        usage="bite <user>",
    )
    async def bite(
        self,
        ctx: Context,
        target: discord.Member = commands.parameter(converter=FuzzyMember, default=None)
    ) -> None:
        if self.bot.pool is None:
            return log.warning("No pool available.")
        
        if target is None:
            return await ctx.send("❌ | Please provide a user to bite.")
        
        conn = await self.bot.pool.acquire()

        await self._increment_interaction_count(
            await YUser.from_discord_user(conn, ctx.author),
            await YUser.from_discord_user(conn, target),
            "bite"
        )
        
        embed = await self._get_embed(ctx.author, target, "bite")

        await self.bot.pool.release(conn)
        await ctx.send(embed=embed)


async def setup(bot: Yuno) -> None:
    await bot.add_cog(UserInteractionModule(bot))
    log.info("Cog loaded: UserInteractionModule")
