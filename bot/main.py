from __future__ import annotations

import io
import os
import re

import orjson
import asyncio
import pathlib
import logging
import difflib
import datetime
import itertools
import functools
import collections

from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
    Any,
    List,
    Tuple,
    Dict,
    Set,
    Iterable
)

import aiohttp
import asyncpg
import discord
from discord.ext import commands, tasks
from discord import Message, Interaction

from .classes import YEmbed, YUser, YGuild
from .config import Config

if TYPE_CHECKING:
    from discord.ext.commands import Context

log = logging.getLogger(__name__)
config = Config()


class AsyncUserCache:
    def __init__(self) -> None:
        self._cache: Dict[int, YUser] = {}
        self._lock = asyncio.Lock()

    async def get_user(self, db: asyncpg.Connection, user_id: int) -> YUser:
        async with self._lock:
            if user_id not in self._cache:
                await self.upsert_user(db, user_id)

            return self._cache[user_id]
        
    async def upsert_user(self, db: asyncpg.Connection, user_id: int) -> YUser:
        async with self._lock:
            user = await YUser.upsert_user(db, user_id)

            self._cache[user_id] = user

            return user
        
    async def insert_many(self, db: asyncpg.Connection, users: List[YUser]) -> None:
        async with self._lock:
            await YUser.insert_many(db, users)

            for user in users:
                self._cache[user.user_id] = user


class Yuno(commands.Bot):
    def __init__(
        self,
        token: str,
        dns: str,
        *,
        session: Optional[aiohttp.ClientSession] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        intents: discord.Intents,
        **kwargs: Any
    ) -> None:
        super().__init__(
            self.get_prefix,  # type: ignore
            case_insensitive=True,
            owner_ids=config.get_owner_ids(),
            intents=intents, 
        )
        self.token = token
        self.dns = dns
        self.session = session
        self.config = Config()
        self.user_cache = AsyncUserCache()
        self.pool: Optional[asyncpg.pool.Pool] = None

        self.OWNER_IDS: List[int] = self.config.get_owner_ids()
        self._extensions_loaded: asyncio.Event = asyncio.Event()
        self._run_db_migrations: bool = self.config.RUN_DB_MIGRATIONS
        self._extensions = [p.stem for p in pathlib.Path(".").glob("./bot/cogs/*.py")]

        self.cached_users: Dict[int, YUser] = {}
        self.cached_guilds: Dict[int, YGuild] = {}
        self.cached_prefixes: Dict[int, List[str]] = {}

    async def setup_hook(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()

        if self._run_db_migrations:
            sql_path = pathlib.Path("./bot/sql")
            sql_files = sorted(sql_path.glob("*.sql"))

            if self.pool is None:
                self.pool = await asyncpg.create_pool(self.config.get_dsn())

            async with self.pool.acquire() as conn:
                for sql_file in sql_files:
                    with open(sql_file, "r") as f:
                        await conn.execute(f.read())

        for extension in self._extensions:
            await self.load_extension(f"bot.cogs.{extension}")

        self._extensions_loaded.set()

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user} (ID: {self.user.id})")  # type: ignore (user is not None)
        log.info(f"Running on {len(self.guilds)} guilds")

    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def fill_user_cache(self) -> None:
        assert self.pool is not None, "Pool is not initialized."

        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT * FROM users")

        for record in records:
            if record["user_id"] in self.cached_users:
                continue

            user = YUser(record)
            self.cached_users[user.user_id] = user

    async def fill_guild_cache(self) -> None:
        assert self.pool is not None, "Pool is not initialized."

        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT * FROM guilds")
        for record in records:
            if record["guild_id"] in self.cached_guilds:
                continue

            guild = YGuild(record)
            self.cached_guilds[guild.guild_id] = guild

    async def fill_prefix_cache(self) -> None:
        assert self.pool is not None, "Pool is not initialized."

        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT * FROM guilds")

        self.cached_prefixes = {
            record["guild_id"]: [record["prefix"] for record in records if record["guild_id"] == record["guild_id"]]
            for record in records
        }

    async def get_prefix(self, message: discord.Message, /) -> Union[str, List[str]]:
        if not message.guild:
            if match := re.match(re.escape("y"), message.content, re.I):
                return match.group(0)

        if message.guild.id in self.cached_prefixes:  # type: ignore - fuck you!
            regex: re.Pattern[str] = re.compile("|".join(map(re.escape, self.cached_prefixes[message.guild.id])), re.I)  # type: ignore
            if match := regex.match(message.content):
                return match.group(0)

        return commands.when_mentioned(self, message)

    async def add_user(self, user_id: int) -> YUser:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.config.get_dsn())
        
        async with self.pool.acquire() as conn:
            return await self.user_cache.upsert_user(conn, user_id)

    async def find_user(self, user_id: int) -> Optional[YUser]:
        user = self.user_cache._cache.get(user_id)
        if user:
            return user
        
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.config.get_dsn())
        
        async with self.pool.acquire() as conn:
            return await YUser.get_user(conn, user_id)
        
    async def insert_many_users(self, users: List[YUser]) -> None:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.config.get_dsn())
        
        async with self.pool.acquire() as conn:
            await self.user_cache.insert_many(conn, users)

    async def close(self) -> None:
        closables = [self.session, self.pool]

        for closable in closables:
            if closable:
                await closable.close()

        await super().close()

    async def send_self_destructing_message(
        self, ctx: commands.Context, content: str, *, delete_after: float = 10.0
    ) -> None:
        msg = await ctx.send(content)
        await asyncio.sleep(delete_after)
        await msg.delete()


def main() -> None:
    discord.utils.setup_logging()
    token = config.TOKEN

    if not token:
        return log.error("No token provided. Please set the DISCORD_TOKEN environment variable.")

    dsn = config.get_dsn()

    intents = discord.Intents(
        guilds=True,
        members=True,
        messages=True,
        message_content=True,
    )

    async def _startup() -> None:

        async with aiohttp.ClientSession() as session:
            bot = Yuno(token, dsn, session=session, intents=intents)
            await bot.start(token)

    asyncio.run(_startup())


if __name__ == "__main__":
    main()
