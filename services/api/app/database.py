from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg

from .settings import settings


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(settings().database_url) as conn:
        yield conn


def apply_migration(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()
