from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEPLOYMENT_TYPE: str = Field(default="debug")
    SECRET_KEY: str | None = Field(default=None, description="Optional session key; if set must be >=32 chars")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @property
    def DEBUG(self) -> bool:
        return self.DEPLOYMENT_TYPE.lower() == "debug"


Config = Settings


@lru_cache
def get_config() -> Settings:
    return Settings()
