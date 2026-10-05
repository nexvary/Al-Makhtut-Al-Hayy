"""Create consistent snapshots of each SQLite database; run with writes paused for a corpus-wide snapshot."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def backup(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError("Backup destination already exists; preserve existing backup")
    destination.mkdir(parents=True)
    manifest = {}
    for path in sorted(source.glob("*.sqlite3")):
        target = destination / path.name
        with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as origin, closing(sqlite3.connect(target)) as output:
            origin.backup(output)
            if output.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError(f"Database integrity failed: {path.name}")
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        manifest[path.name] = digest.hexdigest()
    if not manifest:
        raise ValueError("No metadata databases found; backup is not complete")
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    backup(args.source, args.destination)
