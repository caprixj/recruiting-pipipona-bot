from typing import List

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration via Pydantic Settings.

    Loads variables from the environment and provides type-safe access
    to database credentials, bot tokens, and infrastructure settings.
    """

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Bot
    BOT_TOKEN: SecretStr
    ADMIN_IDS: List[int] = []

    # Database
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: SecretStr
    DB_NAME: str

    @computed_field
    @property
    def DB_URL(self) -> str:
        """Constructs the AsyncPG connection string."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        """Constructs the Redis connection string."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
