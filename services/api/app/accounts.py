"""Local account lifecycle for light deployments; passwords never enter audit records."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from threading import Lock
from uuid import uuid4

from .auth import Role

_password_lock = Lock()


def password_hash(password: str, salt: bytes | None = None) -> str:
    if not 12 <= len(password) <= 1024:
        raise ValueError("Password must contain 12 to 1024 characters")
    salt = salt or os.urandom(16)
    with _password_lock:
        digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32, maxmem=32*1024*1024)
    return base64.b64encode(salt + digest).decode()


class AccountRepository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS accounts_schema(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO accounts_schema VALUES(1);
                CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, username TEXT UNIQUE,
                  role TEXT, active INTEGER, version INTEGER, password_hash TEXT);
                CREATE TABLE IF NOT EXISTS account_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  account_id TEXT, actor TEXT, action TEXT, before_json TEXT, after_json TEXT, timestamp TEXT);
            ''')
            connection.commit()
        path.chmod(0o600)

    @staticmethod
    def public(row):
        return dict(zip(("id", "username", "role", "active", "version"), row[:5])) if row else None

    @staticmethod
    def audit(connection, identifier, actor, action, before, after):
        connection.execute("INSERT INTO account_audit(account_id,actor,action,before_json,after_json,timestamp) VALUES(?,?,?,?,?,?)",
                           (identifier,actor,action,json.dumps(before),json.dumps(after),datetime.now(UTC).isoformat()))

    def create(self, username: str, role: Role, password: str, *, actor: str, bootstrap=False):
        hashed = password_hash(password)
        identifier = str(uuid4())
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if bootstrap and (role != Role.ADMIN or connection.execute("SELECT count(*) FROM accounts").fetchone()[0]):
                raise ValueError("Bootstrap is allowed only for an empty account database")
            try:
                connection.execute("INSERT INTO accounts VALUES(?,?,?,?,?,?)", (identifier,username.casefold(),role.value,1,1,hashed))
            except sqlite3.IntegrityError as exc:
                raise ValueError("Username already exists") from exc
            result = self.public(connection.execute("SELECT * FROM accounts WHERE id=?", (identifier,)).fetchone())
            self.audit(connection,identifier,actor,"create",None,result)
            return result

    def get(self, identifier: str):
        with closing(sqlite3.connect(self.path)) as connection:
            return self.public(connection.execute("SELECT * FROM accounts WHERE id=?", (identifier,)).fetchone())

    def list(self):
        with closing(sqlite3.connect(self.path)) as connection:
            return [self.public(row) for row in connection.execute("SELECT * FROM accounts ORDER BY username LIMIT 1000")]

    def authenticate(self, username: str, password: str):
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute("SELECT * FROM accounts WHERE username=?", (username.casefold(),)).fetchone()
        # Run the same password KDF for unknown/inactive users; do not disclose account existence.
        encoded = base64.b64decode(row[5]) if row else b"\x00"*48
        valid_length = 12 <= len(password) <= 1024
        if not valid_length:
            password = "invalid-password"
        candidate = base64.b64decode(password_hash(password, encoded[:16]))[16:]
        if not valid_length or not row or not row[3] or not hmac.compare_digest(candidate,encoded[16:]):
            return None
        return self.public(row)

    def change(self, identifier: str, *, actor: str, role: Role | None = None, active: bool | None = None, password: str | None = None):
        hashed = password_hash(password) if password is not None else None
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM accounts WHERE id=?", (identifier,)).fetchone()
            if not row:
                raise ValueError("Account not found")
            next_role, next_active = role.value if role else row[2], int(active) if active is not None else row[3]
            if (row[2] == Role.ADMIN and row[3] and (next_role != Role.ADMIN or not next_active)
                    and connection.execute("SELECT count(*) FROM accounts WHERE role='admin' AND active=1").fetchone()[0] <= 1):
                raise ValueError("Cannot remove the last active Administrator")
            before = self.public(row)
            connection.execute("UPDATE accounts SET role=?,active=?,version=version+1,password_hash=? WHERE id=?",
                               (next_role,next_active,hashed or row[5],identifier))
            after = self.public(connection.execute("SELECT * FROM accounts WHERE id=?", (identifier,)).fetchone())
            self.audit(connection,identifier,actor,"password-reset" if hashed else "permissions",before,after)
            return after

    def audit_records(self):
        with closing(sqlite3.connect(self.path)) as connection:
            return [dict(zip(("account_id","actor","action","before","after","timestamp"),row))
                    for row in connection.execute("SELECT account_id,actor,action,before_json,after_json,timestamp FROM account_audit ORDER BY sequence DESC LIMIT 1000")]


@lru_cache(maxsize=1)
def account_repository():
    return AccountRepository(Path(os.getenv("ACCOUNT_METADATA_PATH", "./data/accounts.sqlite3")))


if __name__ == "__main__":
    import argparse
    import getpass
    import re

    parser = argparse.ArgumentParser(description="Create the first Administrator; no default password")
    parser.add_argument("action", choices=["bootstrap"])
    parser.add_argument("--username", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,100}",args.username):
        parser.error("Username must use 3-100 letters/digits or _.@-")
    password = getpass.getpass("Administrator password (12+ characters): ")
    if password != getpass.getpass("Repeat password: "):
        parser.error("Passwords differ")
    result = account_repository().create(args.username,Role.ADMIN,password,actor="local-bootstrap",bootstrap=True)
    print(json.dumps(result))
