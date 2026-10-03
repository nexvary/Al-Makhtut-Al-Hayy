from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO, Protocol


class ObjectStore(Protocol):
    def put(self, stream: BinaryIO, *, suffix: str = "") -> str: ...
    def open(self, key: str) -> BinaryIO: ...
    def exists(self, key: str) -> bool: ...


class LocalObjectStore:
    """Content-addressed local implementation behind the production storage contract."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, stream: BinaryIO, *, suffix: str = "") -> str:
        data = stream.read()
        digest = hashlib.sha256(data).hexdigest()
        safe_suffix = "".join(char for char in suffix if char.isalnum() or char in {".", "-", "_"})
        key = f"{digest}{safe_suffix}"
        target = self.root / key
        if not target.exists():
            target.write_bytes(data)
        return key

    def open(self, key: str) -> BinaryIO:
        if "/" in key or "\\" in key or key in {".", ".."}:
            raise ValueError("Invalid object key")
        return (self.root / key).open("rb")

    def exists(self, key: str) -> bool:
        if "/" in key or "\\" in key:
            return False
        return (self.root / key).is_file()
