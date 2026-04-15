import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "secDB FastAPI"
    app_version: str = "1.0.0"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    database_url: str

    def __init__(self) -> None:
        raw_database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/secDB?schema=public",
        )
        self.database_url = self._to_sqlalchemy_url(raw_database_url)
        self.secret_key = os.getenv("JWT_SECRET", "change_me_fastapi")

    @staticmethod
    def _to_sqlalchemy_url(url: str) -> str:
        cleaned = url.split("?")[0]
        if cleaned.startswith("postgresql://"):
            return cleaned.replace("postgresql://", "postgresql+psycopg://", 1)
        return cleaned


@lru_cache
def get_settings() -> Settings:
    return Settings()
