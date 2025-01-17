from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import (TYPE_CHECKING, NamedTuple, Optional, Protocol, Type,
                    TypedDict, TypeVar, runtime_checkable)

from discord.ext import commands

from ..utils import MessagePreview

if TYPE_CHECKING:
    from discord import Guild, User
    from discord.ext.commands import Context

    from ..main import Yuno
    from .embed import YEmbed


T = TypeVar("T")
P = TypeVar("P")

log = logging.getLogger(__name__)


__all__: tuple[str, ...] = (
    "YunoError",
    "YunoCommandError",
    "YunoCommandOnCooldown",
    "YunoCommandCancelled",
    "YunoCommandSuccess",
    "YunoCommandNeutral",
    "YunoCommandErrorType",
    "YunoCommandErrorFactory",
    "YunoColours",
    "Palette",
    "PaletteColour",
)


class PaletteColour(NamedTuple):
    hex: int
    rgb: tuple[int, ...]


class Palette(TypedDict):
    success: PaletteColour
    error: PaletteColour
    neutral: PaletteColour
    pending: PaletteColour
    cancelled: PaletteColour


class YunoColours:
    def __init__(self, palette: Palette) -> None:
        self.palette = palette

    def __getattr__(self, name: str) -> tuple[int, tuple[int, ...]]:
        return self.palette[name]

    @classmethod
    def friday_palette(cls) -> Palette:
        """>>> credits: https://www.color-hex.com/color-palette/1053754
        #facea8	(250,206,168) -> neutral
        #99b898	(153,184,152) -> success
        #ff847c	(255,132,124) -> pending
        #e84a5f	(232,74,95) -> error
        #2a363b	(42,54,59) -> cancelled
        """
        return Palette(
            success=PaletteColour(0x99B898, (153, 184, 152)),
            error=PaletteColour(0xE84A5F, (232, 74, 95)),
            neutral=PaletteColour(0xFACEA8, (250, 206, 168)),
            pending=PaletteColour(0xFF847C, (255, 132, 124)),
            cancelled=PaletteColour(0x2A363B, (42, 54, 59)),
        )


class YunoError(Exception):
    def __init__(self, message: str, level: str = "error") -> None:
        self.message = message
        self.level = level

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"<YunoError level={self.level!r} message={self.message!r}>"


class YunoCommandError(commands.CommandError, YunoError):
    def get_colour(self, palette: Optional[Palette] = None) -> tuple[int, tuple[int, ...]]:
        if palette is None:
            return YunoColours.friday_palette()[self.level]
        return palette[self.level]

    async def send_timed_response(self, ctx: Context[Yuno], message: str, time: int = 5) -> None:
        async with MessagePreview(ctx, message) as _:
            return await asyncio.sleep(time)

    def log_case(self, message: str) -> None:
        log.error(message)

    def create_embed(self, ctx: Context[Yuno]) -> YEmbed:
        return YEmbed.error(
            title=f"Command Exception: {self.level.capitalize()}",
            description=self.message,
            color=self.get_colour()[0],
        )

    async def handle(self, ctx: Context[Yuno], message: Optional[str] = None) -> None:
        if message is not None:
            self.log_case(message)

        await self.send_timed_response(ctx, self.message)


class YunoCommandOnCooldown(YunoCommandError):
    def __init__(self, message: str, level: str = "pending") -> None:
        super().__init__(message, level)


class YunoCommandCancelled(YunoCommandError):
    def __init__(self, message: str, level: str = "cancelled") -> None:
        super().__init__(message, level)


class YunoCommandSuccess(YunoCommandError):
    def __init__(self, message: str, level: str = "success") -> None:
        super().__init__(message, level)


class YunoCommandNeutral(YunoCommandError):
    def __init__(self, message: str, level: str = "neutral") -> None:
        super().__init__(message, level)


class YunoCommandErrorType(Enum):
    ERROR = "error"
    SUCCESS = "success"
    NEUTRAL = "neutral"
    PENDING = "pending"
    CANCELLED = "cancelled"


class YunoCommandErrorFactory:
    def __init__(self, level: YunoCommandErrorType) -> None:
        self.level = level

    def __call__(self, message: str) -> Type[YunoCommandError]:
        return {
            YunoCommandErrorType.ERROR: YunoCommandError,
            YunoCommandErrorType.SUCCESS: YunoCommandSuccess,
            YunoCommandErrorType.NEUTRAL: YunoCommandNeutral,
            YunoCommandErrorType.PENDING: YunoCommandOnCooldown,
            YunoCommandErrorType.CANCELLED: YunoCommandCancelled,
        }[self.level](message)

    def __repr__(self) -> str:
        return f"<YunoCommandErrorFactory level={self.level!r}>"

    def __str__(self) -> str:
        return self.level.value

    @staticmethod
    def error(message: str) -> YunoCommandError:
        return YunoCommandError(message)

    @staticmethod
    def success(message: str) -> YunoCommandSuccess:
        return YunoCommandSuccess(message)

    @staticmethod
    def neutral(message: str) -> YunoCommandNeutral:
        return YunoCommandNeutral(message)

    @staticmethod
    def pending(message: str) -> YunoCommandOnCooldown:
        return YunoCommandOnCooldown(message)

    @staticmethod
    def cancelled(message: str) -> YunoCommandCancelled:
        return YunoCommandCancelled(message)
