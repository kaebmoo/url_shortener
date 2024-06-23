# gogoth/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

# โหลดค่าจาก .env
load_dotenv()


class Settings(BaseSettings):

    env_name: str = "Local"
    base_url: str = os.getenv('BASE_URL', 'http://localhost:8000')
    db_url: str = os.getenv('DB_URL', 'sqlite:///./shortener.db')
    secret_key: str = os.getenv('SECRET_KEY', 'default_secret_key')  # เพิ่ม SECRET_KEY
    db_api: str = os.getenv('DB_API', 'sqlite:///./user_management/data-dev.sqlite')
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:

    settings = Settings()
    print(f"Loading settings for: {settings.env_name}")

    return settings

# Settings Variable 	Environment Variable 	Value
# env_name 	ENV_NAME 	Name of your current environment
# base_url 	BASE_URL 	Domain of your app
# db_url 	DB_URL 	Address of your database
# https://realpython.com/build-a-python-url-shortener-with-fastapi/#step-1-prepare-your-environment