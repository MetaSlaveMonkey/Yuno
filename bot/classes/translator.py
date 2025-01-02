from __future__ import annotations

from typing import Any, Optional, TypeVar, TypedDict

import orjson
import asyncio
import aiofiles

from pathlib import Path

__all__: tuple[str, ...] = ("Translator",)


T = TypeVar("T")


class HelpSection(TypedDict):
    description: str
    usage: str

class SubCommandMessages(TypedDict, total=False):
    success: str
    fail: str
    fallback_error: str

class SubCommands(TypedDict, total=False):
    language: SubCommandMessages
    timezone: SubCommandMessages

class Command(TypedDict, total=False):
    description: list[str]
    emoji: str
    footer: str
    message: Optional[str]
    errors: Optional[dict[str, str]]
    help: Optional[HelpSection]
    aliases: Optional[list[str]]
    subcommands: Optional[SubCommands]

class UserCommands(TypedDict):
    pat: Command
    lick: Command
    poke: Command
    time: Command
    ping: Command
    help: Command
    userset: Command
    leaderboard: Command

class Interaction(TypedDict, total=False):
    success: str
    fail: str
    message: Optional[str]

class LocaleTranslations(TypedDict):
    commands: UserCommands
    errors: dict[str, str]
    general: dict[str, str | dict[str, str]]
    settings: dict[str, dict[str, str]]
    interactions: Optional[dict[str, Interaction]]

class Translations(TypedDict):
    en_US: LocaleTranslations


class Translator:
    def __init__(self, path: str | Path) -> None:
        self._file_path = path
        self.translations: Optional[Translations] = None

    async def load_translations(self) -> None:
        try:
            async with aiofiles.open(self._file_path, mode="rb") as f:
                content = await f.read()
                self.translations = orjson.loads(content)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Translation file not found: {self._file_path}") from e
        except orjson.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from file: {self._file_path}") from e
        
    def get_translation(
        self,
        key: str,
        locale: str = "en_US"
    ) -> str:
        if self.translations is None:
            raise ValueError("Translations not loaded. Call 'load_translations' first.")

        if locale not in self.translations:
            raise ValueError(f"Locale '{locale}' not supported.")
        
        keys = key.split(".")
        translation = self.translations[locale]
        current_node = translation

        for key in keys:
            if key not in current_node:
                raise KeyError(f"Key '{key}' not found in translation file.")
            
            current_node = current_node[key]

        if not isinstance(current_node, str):
            raise ValueError("Key does not point to a string value.")
        
        return current_node
        
    async def reload_translations(self) -> None:
        await self.load_translations()

    def is_valid_locale(self, locale: str) -> bool:
        return self.translations is not None and locale in self.translations


async def main() -> None:
    translator = Translator(path="data/translation.json")
    await translator.load_translations()

    reset_success = translator.get_translation(
        key="user_commands.time.message", 
        locale="en_US",
    )


    print(reset_success.format(time="5 pm", user="Yuno"))


if __name__ == "__main__":
    asyncio.run(main())