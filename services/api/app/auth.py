from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable
from enum import StrEnum

from fastapi import Header, HTTPException

from .settings import settings


class Role(StrEnum):
    VIEWER = "viewer"
    TRANSCRIBER = "transcriber"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    READER = "reader"
    STUDENT = "student"
    RESEARCHER = "researcher"
    EDITOR = "editor"
    ADMINISTRATOR = "admin"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(subject: str, role: Role, *, ttl_seconds: int = 3600, account_id: str | None = None, session_version: int | None = None) -> str:
    payload = {
        "sub": subject,
        "role": role.value,
        "exp": int(time.time()) + ttl_seconds,
    }
    if account_id is not None:
        payload.update(account_id=account_id, session_version=session_version)
    encoded = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings().auth_secret.encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded}.{_b64(signature)}"


def verify_token(token: str) -> dict:
    try:
        encoded, supplied_signature = token.split(".", 1)
        expected = hmac.new(
            settings().auth_secret.encode("utf-8"),
            encoded.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _unb64(supplied_signature)):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(encoded))
        if int(payload["exp"]) <= int(time.time()):
            raise ValueError("expired")
        Role(payload["role"])
        if not isinstance(payload.get("sub"), str) or not payload["sub"].strip():
            raise ValueError("invalid subject")
        if "account_id" in payload:
            from .accounts import account_repository
            account = account_repository().get(payload["account_id"])
            if not account or not account["active"] or account["version"] != payload.get("session_version") or account["role"] != payload["role"] or account["username"] != payload["sub"]:
                raise ValueError("revoked account session")
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token") from exc


def require_roles(*allowed: Role) -> Callable:
    def dependency(authorization: str | None = Header(default=None)) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token required")
        payload = verify_token(authorization.removeprefix("Bearer ").strip())
        if Role(payload["role"]) not in set(allowed):
            raise HTTPException(status_code=403, detail="Insufficient role")
        if "account_id" in payload:
            from .accounts import account_repository
            account = account_repository().get(payload["account_id"])
            if not account or not account["active"] or account["version"] != payload.get("session_version") or account["role"] != payload["role"] or account["username"] != payload["sub"]:
                raise ValueError("revoked account session")
        return payload

    return dependency
