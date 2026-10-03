from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("APP_ENV", "development")
    auth_secret: str = os.getenv(
        "AUTH_SECRET",
        "development-change-me-please-use-a-real-secret",
    )
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://makhtut:makhtut@localhost:5432/makhtut",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    object_store_path: str = os.getenv("OBJECT_STORE_PATH", "./data/objects")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))


def settings() -> Settings:
    return Settings()


def validate_production_settings(value: Settings) -> None:
    if value.environment == "production":
        if value.auth_secret.startswith("development-") or len(value.auth_secret) < 32:
            raise RuntimeError("Production AUTH_SECRET must be a strong secret of at least 32 characters")
        if "makhtut:makhtut@" in value.database_url:
            raise RuntimeError("Production DATABASE_URL must not use development credentials")
