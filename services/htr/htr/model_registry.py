from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel


class HtrModelRecord(BaseModel):
    id: str
    engine: str
    path: str
    sha256: str
    description: str | None = None
    license: str | None = None
    source_url: str | None = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_local_model(
    path: Path,
    *,
    model_id: str,
    engine: str = "kraken",
    license: str | None = None,
    source_url: str | None = None,
) -> HtrModelRecord:
    if not path.is_file():
        raise FileNotFoundError(path)
    return HtrModelRecord(
        id=model_id,
        engine=engine,
        path=str(path),
        sha256=sha256_file(path),
        license=license,
        source_url=source_url,
    )
