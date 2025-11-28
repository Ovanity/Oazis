"""Application settings loaded from environment variables."""

from functools import lru_cache
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed configuration for the Oazis bot."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: SecretStr = Field(
        ...,
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN"),
        description="Token provided by BotFather.",
    )
    database_url: str = Field(
        default="sqlite:///./data/oazis.db",
        validation_alias=AliasChoices("DATABASE_URL", "OAZIS_DATABASE_URL"),
    )
    timezone: str = Field(
        default="Europe/Paris",
        validation_alias=AliasChoices("TIMEZONE", "TZ"),
        description="IANA timezone used for scheduling reminders.",
    )
    debug: bool = Field(default=False, validation_alias=AliasChoices("DEBUG", "OAZIS_DEBUG"))
    hydration_start_hour: int = Field(default=9, ge=0, le=23)
    hydration_end_hour: int = Field(default=21, ge=0, le=23)
    reminder_interval_minutes: int = Field(default=90, gt=0)
    default_daily_target_ml: int = Field(default=2000, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

