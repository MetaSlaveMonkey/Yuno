from __future__ import annotations

import logging
from time import time
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import discord
from discord import utils
from discord import message
from discord.ext import commands

from ..classes import YUser

if TYPE_CHECKING:
    from ..main import Yuno
    

log = logging.getLogger(__name__)


class DiscordUserSettings(commands.Cog, name="⚙ Settings"):
    def __init__(self, bot: Yuno) -> None:
        self.bot = bot

    def _is_valid_timezone(self, timezone: str) -> bool:
        try:
            ZoneInfo(timezone)
        except Exception:
            return False
        return True
    
    async def _cache_user(self, user_id: int) -> YUser:
        async with self.bot.pool.acquire() as conn:
            user = await self.bot.user_cache.fetch_user(conn, user_id)
            await self.bot.user_cache.set_user(user)
        return user
    
    @commands.group(name="user-settings", aliases=["usersettings", "uset"])
    async def user_settings(self, ctx: commands.Context) -> Optional[discord.Message]:
        user = await self._cache_user(ctx.author.id)

        if ctx.invoked_subcommand is None:
            message = self.bot.translator.get_translation(
                key="user_commands.userset.subcommands.fail",
                locale=user.locale
            )

            return await ctx.send(f"❌ | {message}")

    @user_settings.command(name="timezone", aliases=["tz"])
    async def set_timezone(self, ctx: commands.Context, timezone: str) -> Optional[discord.Message]:
        user = await self._cache_user(ctx.author.id)

        if not self._is_valid_timezone(timezone):
            message = self.bot.translator.get_translation(
                key="user_commands.userset.subcommands.timezone.fail",
                locale=user.locale
            )

            return await ctx.send(f"❌ | {message.format(timezone=timezone)}")

        user.time_zone = timezone
        await self.bot.user_cache.set_user(user)

        async with self.bot.pool.acquire() as conn:
            await YUser.upsert_user(conn, user.user_id, time_zone=timezone, locale=user.locale)

        message = self.bot.translator.get_translation(
            key="user_commands.userset.subcommands.timezone.success",
            locale=user.locale
        )

        return await ctx.send(f"✅ | {message.format(timezone=timezone)}")
    
    @user_settings.command(name="language", aliases=["lang", "locale"])
    async def set_language(self, ctx: commands.Context, language: str) -> Optional[discord.Message]:
        user = await self._cache_user(ctx.author.id)

        if not self.bot.translator.is_valid_locale(language):
            message = self.bot.translator.get_translation(
                key="user_commands.userset.subcommands.language.fail",
                locale=user.locale,
            )

            return await ctx.send(f"❌ | {message.format(language=language)}")
        
        user.locale = language
        await self.bot.user_cache.set_user(user)

        async with self.bot.pool.acquire() as conn:
            await YUser.upsert_user(conn, user.user_id, time_zone=user.time_zone, locale=language)

        message = self.bot.translator.get_translation(
            key="user_commands.userset.subcommands.language.success",
            locale=user.locale,
        )

        return await ctx.send(f"✅ | {message.format(language=language)}")
    

async def setup(bot: Yuno) -> None:
    await bot.add_cog(DiscordUserSettings(bot))
    log.info("Cog loaded: DiscordUserSettings")
