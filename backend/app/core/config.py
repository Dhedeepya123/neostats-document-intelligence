from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory:
# C:\Users\dhede\Documents\neostats-document-intelligence
BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Neostats Document Intelligence"
    app_version: str = "1.0.0"

    database_url: str

    ai_api_key: str = ""

    max_file_size_mb: int = 10
    max_pages: int = 3

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

