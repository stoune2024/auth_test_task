from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    DB_HOST: str = Field(default="postgres")
    DB_PORT: str = Field(default="5432")
    DB_USER: str = Field(default="postgres")
    DB_PASS: str = Field(default="postgres")
    DB_NAME: str = Field(default="authdb")
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    model_config = SettingsConfigDict(
        env_file=f"{os.path.dirname(os.path.abspath(__file__))}/../.env"
    )

    @property
    def db_url(self):
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()


@lru_cache()
def get_settings():
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]
