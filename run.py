import argparse
import asyncio
import os
from contextlib import suppress

from dotenv import load_dotenv

from bot.main import main as bot_starter_function

load_dotenv()


def main():
    print(
        f"""
       ▓██   ██▓ █    ██  ███▄    █  ▒█████ 
       ▒██  ██▒ ██  ▓██▒ ██ ▀█   █ ▒██▒  ██▒   
       ▒██ ██░▓██  ▒██░▓██  ▀█ ██▒▒██░  ██▒
       ░ ▐██▓░▓▓█  ░██░▓██▒  ▐▌██▒▒██   ██░
       ░ ██▒▓░▒▒█████▓ ▒██░   ▓██░░ ████▓▒░    
       ██▒▒▒ ░▒▓▒ ▒ ▒ ░ ▒░   ▒ ▒ ░ ▒░▒░▒░      
       ▓██ ░▒░ ░░▒░ ░ ░ ░ ░░   ░ ▒░  ░ ▒ ▒░ 
       ▒ ▒ ░░   ░░░ ░ ░    ░   ░ ░ ░ ░ ░ ▒  
       ░ ░        ░              ░     ░ ░  
       ░ ░  
    """
    )

    bot_starter_function()


if __name__ == "__main__":
    with suppress(
        KeyboardInterrupt,
        SystemExit,
        asyncio.exceptions.CancelledError,
    ):
        main()
