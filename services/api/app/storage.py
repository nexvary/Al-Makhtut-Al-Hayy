from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import BinaryIO, Protocol


class StorageProvider(Protocol):
    def put(self, stream: BinaryIO, *, suffix: str = "") -> str: ...
    def open(self, key: str) -> BinaryIO: ...
    def exists(self, key: str) -> bool: ...


# Preserve existing imports while exposing the future S3/R2/MinIO provider boundary.
ObjectStore = StorageProvider


class StorageLimitExceeded(ValueError):
    pass


class LocalObjectStore:
    """Bounded streaming, content-addressed writes for the single-worker light profile."""

    def __init__(self, root: Path, *, max_object_bytes: int = 128 * 1024 * 1024,
                 max_total_bytes: int = 5 * 1024 * 1024 * 1024) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_object_bytes = max_object_bytes
        self.max_total_bytes = max_total_bytes
        self._lock = RLock()

    def put(self, stream: BinaryIO, *, suffix: str = "") -> str:
        safe_suffix = "".join(char for char in suffix if char.isalnum() or char in {".", "-", "_"})[:32]
        temporary = None
        with self._lock:
            try:
                digest = hashlib.sha256()
                length = 0
                with tempfile.NamedTemporaryFile(dir=self.root, prefix=".pending-", delete=False) as output:
                    temporary = Path(output.name)
                    while chunk := stream.read(64 * 1024):
                        length += len(chunk)
                        if length > self.max_object_bytes:
                            raise StorageLimitExceeded("Object exceeds the configured import limit")
                        digest.update(chunk)
                        output.write(chunk)
                    output.flush()
                    os.fsync(output.fileno())
                key = f"{digest.hexdigest()}{safe_suffix}"
                target = self.root / key
                if not target.exists():
                    total = sum(p.stat().st_size for p in self.root.iterdir() if p.is_file() and not p.name.startswith(".pending-"))
                    if total + length > self.max_total_bytes:
                        raise StorageLimitExceeded("Local object storage quota reached")
                    os.replace(temporary, target)
                return key
            finally:
                if temporary:
                    temporary.unlink(missing_ok=True)

    def open(self, key: str) -> BinaryIO:
        if not key or "/" in key or "\\" in key or key in {".", ".."}:
            raise ValueError("Invalid object key")
        return (self.root / key).open("rb")

    def exists(self, key: str) -> bool:
        if not key or "/" in key or "\\" in key or key in {".", ".."}:
            return False
        return (self.root / key).is_file()
