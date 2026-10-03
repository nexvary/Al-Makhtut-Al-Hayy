import io
from pathlib import Path

import pytest

from app.auth import Role, issue_token, verify_token
from app.storage import LocalObjectStore


def test_signed_token_round_trip() -> None:
    token = issue_token("reviewer-1", Role.REVIEWER)
    payload = verify_token(token)
    assert payload["sub"] == "reviewer-1"
    assert payload["role"] == "reviewer"


def test_object_store_is_content_addressed(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path)
    key1 = store.put(io.BytesIO(b"abc"), suffix=".bin")
    key2 = store.put(io.BytesIO(b"abc"), suffix=".bin")
    assert key1 == key2
    assert store.open(key1).read() == b"abc"
    with pytest.raises(ValueError):
        store.open("../escape")
