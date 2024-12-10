import os
import asyncio
import argparse

from dotenv import load_dotenv
from contextlib import suppress

from bot.main import main as bot_starter_function


load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Run the bot.")
    parser.add_argument('--discord_token', default=os.getenv('DISCORD_TOKEN'), help='Discord bot token')
    parser.add_argument('--postgres_user', default=os.getenv('POSTGRES_USER'), help='PostgreSQL user')
    parser.add_argument('--postgres_password', default=os.getenv('POSTGRES_PASSWORD'), help='PostgreSQL password')
    parser.add_argument('--postgres_db', default=os.getenv('POSTGRES_DB'), help='PostgreSQL database name')
    parser.add_argument('--postgres_host', default=os.getenv('POSTGRES_HOST'), help='PostgreSQL host')
    parser.add_argument('--postgres_port', default=os.getenv('POSTGRES_PORT'), help='PostgreSQL port')
    parser.add_argument('--owner_ids', default=os.getenv('OWNER_IDS'), help='Comma-separated list of owner IDs')
    parser.add_argument('--run_db_migrations', type=int, default=int(os.getenv('RUN_DB_MIGRATIONS', 0)), help='Run database migrations (1 to run, 0 to skip)')

    args = parser.parse_args()

    print(f"""
       ▓██   ██▓ █    ██  ███▄    █  ▒█████    Made by 54b3r
       ▒██  ██▒ ██  ▓██▒ ██ ▀█   █ ▒██▒  ██▒   
       ▒██ ██░▓██  ▒██░▓██  ▀█ ██▒▒██░  ██▒    Credits:
       ░ ▐██▓░▓▓█  ░██░▓██▒  ▐▌██▒▒██   ██░    - bhv_permaban
       ░ ██▒▓░▒▒█████▓ ▒██░   ▓██░░ ████▓▒░    
       ██▒▒▒ ░▒▓▒ ▒ ▒ ░ ▒░   ▒ ▒ ░ ▒░▒░▒░      
       ▓██ ░▒░ ░░▒░ ░ ░ ░ ░░   ░ ▒░  ░ ▒ ▒░ 
       ▒ ▒ ░░   ░░░ ░ ░    ░   ░ ░ ░ ░ ░ ▒  
       ░ ░        ░              ░     ░ ░  
       ░ ░  

       PostgreSQL User: {args.postgres_user}
       PostgreSQL Database: {args.postgres_db}
       Owner IDs: {args.owner_ids}
       Run DB Migrations: {args.run_db_migrations}
    """
    )

    bot_starter_function()


if __name__ == '__main__':
    with suppress(
        KeyboardInterrupt,
        SystemExit,
        asyncio.exceptions.CancelledError,
    ):
        main()
