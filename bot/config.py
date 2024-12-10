import os
import logging
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Bot Configuration"""

    TOKEN = os.getenv('DISCORD_TOKEN')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASS = os.getenv('POSTGRES_PASS')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT')
    OWNER_IDS = os.getenv('OWNER_IDS', '').split(',')
    RUN_DB_MIGRATIONS = os.getenv('RUN_DB_MIGRATIONS', 'False').lower() == 'true'
    DEFAULT_COLOR = 0x2F3136
    VERSION = '0.0.1'

    error_404 = "https://cdn.discordapp.com/attachments/1158643530818920449/1315411542770057226/404-not-found-cute-2048x2048-18164.png"

    @classmethod
    def get_dsn(cls):
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASS}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )
    
    @classmethod
    def get_owner_ids(cls):
        return [int(owner_id) for owner_id in cls.OWNER_IDS]
    
    @classmethod
    def is_owner(cls, user_id):
        return user_id in cls.get_owner_ids()
