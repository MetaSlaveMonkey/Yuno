from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import utils
from discord.ext import commands

from ..classes import YGuild, YUser
from ..utils import FakeRecord

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

        user_chunked = await guild.chunk()
        user_list = [self.bot.get_user(user.id) for user in user_chunked]

        # Don't join bot farm servers ... (why is this even a thing?)
        # Reddit post: https://www.reddit.com/r/discordapp/comments/7k3yff/about_bot_farms/
        # I've stumbled across this post, and was like wtf? Why would someone do this?
        # Anyways ... Here's the code to prevent this.
        legit_users = [
            self.bot.get_user(user.id) for user in user_list if user and not user.bot
        ]
        if legit_users is None:
            log.info(f"Leaving guild {guild.name} ({guild.id})")
            return await guild.leave()
        
            # Note for self: Remeber to put this in the kb.
        if len(legit_users) > 10 or guild.id not in self.bot.cached_guilds:
            log.info(f"Leaving guild {guild.name} ({guild.id} - {len(legit_users)} users)")
            return await guild.leave()
        
        _users = [
            YUser(FakeRecord({"user_id": user.id, "time_zone": "UTC", "locale": "en_US"}))
            for user in legit_users if user is not None
        ]

        await self.bot.insert_many_users(_users)
        log.info(f"Inserted {len(_users)} users into the database")


async def setup(bot: Yuno) -> None:
    await bot.add_cog(DiscordEventHandler(bot))
    log.info("Cog loaded: DiscordEventHandler")
