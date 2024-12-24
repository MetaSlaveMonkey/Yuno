from __future__ import annotations

import asyncio
import collections
import datetime
import difflib
import functools
import io
import itertools
import logging
import os
import pathlib
import re
from typing import TYPE_CHECKING, Any, Dict, DefaultDict, List, Optional, Set, Tuple, Union

import aiohttp
import asyncpg
import discord
from collections import defaultdict
from discord import Interaction, Message
from discord.ext import commands, tasks

from .classes import YEmbed, YGuild, YUser
from .config import Config

if TYPE_CHECKING:
    from discord.ext.commands import Context

log = logging.getLogger(__name__)
config = Config()


class AsyncUserCache:
    def __init__(self) -> None:
        self._cache: Dict[int, YUser] = {}
        self._lock = asyncio.Lock()

    async def set_user(self, user: YUser) -> None:
        async with self._lock:
            self._cache[user.user_id] = user

    async def get_users(self) -> List[YUser]:
        async with self._lock:
            return list(self._cache.values())

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
        intents: discord.Intents,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            command_prefix=self.get_prefix,  # type: ignore
            case_insensitive=True,
            owner_ids=config.get_owner_ids(),
            intents=intents,
            chunk_guilds_at_startup=False,
            max_messages=2000,
            **kwargs,
        )
        self.dns = dns
        self.token = token
        self.session = session
        self.config = Config()
        self._admin_only: bool = False
        self.strip_after_prefix = True
        self.pool: Optional[asyncpg.pool.Pool] = None

        self.OWNER_IDS: List[int] = self.config.get_owner_ids()
        self._extensions_loaded: asyncio.Event = asyncio.Event()
        self._run_db_migrations: bool = self.config.RUN_DB_MIGRATIONS
        self._extensions = [p.stem for p in pathlib.Path(".").glob("./bot/cogs/*.py")]

        self.user_cache = AsyncUserCache()
        self.cached_guilds: Dict[int, YGuild] = {}
        self.cached_prefixes: DefaultDict[int, list[re.Pattern[str]]] = defaultdict(list)

    async def setup_hook(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()

        def serializer(obj: Any) -> str:
            return discord.utils._to_json(obj)

        def deserializer(s: str) -> Any:
            return discord.utils._from_json(s)

        prep_init = self._run_db_migrations

        async def init(conn: asyncpg.Connection) -> None:
            await conn.set_type_codec(
                typename="json",
                encoder=serializer,
                decoder=deserializer,
                schema="pg_catalog",
                format="text",
            )
            if prep_init is not None:
                sql_path = pathlib.Path("./bot/sql")
                sql_files = sorted(sql_path.glob("*.sql"))

                if self.pool is None:
                    self.pool = await asyncpg.create_pool(self.config.get_dsn(), init=init)

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
            if record["user_id"] in self.user_cache._cache:
                continue

            user = YUser(record)
            await self.user_cache.set_user(user)

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
            records = await conn.fetch("SELECT * FROM prefix")

        for record in records:
            if record["guild_id"] in self.cached_prefixes:
                self.cached_prefixes[record["guild_id"]].append(record["prefix"])
            else:
                self.cached_prefixes[record["guild_id"]] = [record["prefix"]]

        log.debug(self.cached_prefixes)

    async def get_prefix(self, message: discord.Message, /) -> Union[str, List[str]]:
        if self.pool is None:
            raise RuntimeError("Bot has not been initialized correctly.")

        if message.guild is None:
            if match := re.match(re.escape('y'), message.content, re.I):
                return match.group(0)

            return commands.when_mentioned_or(*("y", "y "))(self, message)

        if not message.guild.id in self.cached_prefixes:
            prefix_query = "SELECT prefix from prefix WHERE guild_id = $1"
            async with self.pool.acquire() as conn:
                records = await conn.fetch(prefix_query, message.guild.id)
                pattern = re.compile("|".join([re.escape(r["prefix"]) for r in records]), re.I)

                self.cached_prefixes[message.guild.id] = [pattern]

        if match := self.cached_prefixes[message.guild.id][0].match(message.content):
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
        await asyncio.gather(*[c.close() for c in closables if c is not None])

        await super().close()


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
