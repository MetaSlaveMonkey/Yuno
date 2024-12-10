from __future__ import annotations

import logging

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from ..classes import YGuild

if TYPE_CHECKING:
    from ..main import Yuno

log = logging.getLogger(__name__)


class DiscordEventHandler(commands.Cog, name="Discord Event Handler"):
    def __init__(self, bot: Yuno) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        if self.bot.pool is None:
            return log.warning("No pool available.")
        
        async with self.bot.pool.acquire() as conn:
            _guild = await YGuild.upsert_guild(conn, guild.id)
            self.bot.cached_guilds[guild.id] = _guild
            
            log.info(f"Joined guild {guild.name} ({guild.id})")


async def setup(bot: Yuno) -> None:
    await bot.add_cog(DiscordEventHandler(bot))
    log.info("Cog loaded: DiscordEventHandler")
