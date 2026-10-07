"""Durable compatibility storage; legacy schemas remain distinct from reviewed living layers."""
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


class LegacyRecordStore:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(os.getenv("LEGACY_METADATA_PATH", "./data/legacy.sqlite3"))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS legacy_schema(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO legacy_schema VALUES(1);
                CREATE TABLE IF NOT EXISTS legacy_records(kind TEXT, id TEXT, payload TEXT, PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS legacy_history(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  kind TEXT, id TEXT, payload TEXT, actor TEXT, timestamp TEXT);
                CREATE TABLE IF NOT EXISTS legacy_audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  kind TEXT, id TEXT, actor TEXT, before_sha256 TEXT, after_sha256 TEXT, timestamp TEXT);
                CREATE TABLE IF NOT EXISTS legacy_editorial(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  id TEXT UNIQUE, scope TEXT, payload TEXT, audit TEXT);
            ''')
            connection.commit()

    def put(self, kind: str, identifier: str, payload: dict, *, actor: str = "legacy-adapter"):
        encoded = json.dumps(payload,ensure_ascii=False,sort_keys=True)
        timestamp = datetime.now(UTC).isoformat()
        with closing(sqlite3.connect(self.path,timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT payload FROM legacy_records WHERE kind=? AND id=?",(kind,identifier)).fetchone()
            connection.execute("INSERT INTO legacy_records VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET payload=excluded.payload",(kind,identifier,encoded))
            connection.execute("INSERT INTO legacy_history(kind,id,payload,actor,timestamp) VALUES(?,?,?,?,?)",(kind,identifier,encoded,actor,timestamp))
            before = hashlib.sha256(previous[0].encode()).hexdigest() if previous else None
            connection.execute("INSERT INTO legacy_audit(kind,id,actor,before_sha256,after_sha256,timestamp) VALUES(?,?,?,?,?,?)",
                               (kind,identifier,actor,before,hashlib.sha256(encoded.encode()).hexdigest(),timestamp))

    def iter_rows(self, kind: str, limit: int = 2000):
        with closing(sqlite3.connect(self.path)) as connection:
            for row in connection.execute("SELECT payload FROM legacy_records WHERE kind=? ORDER BY rowid DESC LIMIT ?",(kind,limit)):
                yield json.loads(row[0])

    def rows(self, kind: str):
        with closing(sqlite3.connect(self.path)) as connection:
            return [json.loads(row[0]) for row in connection.execute("SELECT payload FROM legacy_records WHERE kind=? ORDER BY rowid",(kind,))]

    def history(self, kind: str, identifier: str):
        with closing(sqlite3.connect(self.path)) as connection:
            return [json.loads(row[0]) for row in connection.execute("SELECT payload FROM legacy_history WHERE kind=? AND id=? ORDER BY sequence",(kind,identifier))]

    def editorial_append(self, scope: str, identifier: str, parent: str | None, payload: str, audit: str):
        with closing(sqlite3.connect(self.path,timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            head = connection.execute("SELECT id FROM legacy_editorial WHERE scope=? ORDER BY sequence DESC LIMIT 1",(scope,)).fetchone()
            if parent != (head[0] if head else None):
                raise ValueError("Revision parent must point to the current head")
            try:
                connection.execute("INSERT INTO legacy_editorial(id,scope,payload,audit) VALUES(?,?,?,?)",(identifier,scope,payload,audit))
            except sqlite3.IntegrityError as exc:
                raise ValueError("Editorial revision identity is immutable") from exc

    def editorial_history(self, scope: str):
        with closing(sqlite3.connect(self.path)) as connection:
            return [row[0] for row in connection.execute("SELECT payload FROM legacy_editorial WHERE scope=? ORDER BY sequence",(scope,))]

    def editorial_audit(self):
        with closing(sqlite3.connect(self.path)) as connection:
            return [row[0] for row in connection.execute("SELECT audit FROM legacy_editorial ORDER BY sequence")]
