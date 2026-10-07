"""Bounded thumbnail fingerprint search. Candidate resemblance is not historical attribution."""
from __future__ import annotations

import base64
import binascii
import hashlib
import heapq
import io
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field

from .living import LayerProvenance
from .visual_search import VisualMatch, VisualQuery, VisualQueryKind

MODEL = "dhash-64-thumbnail-v1"
MAX_IMAGE_BYTES = 1024 * 1024
MAX_PIXELS = 1024 * 1024
_processing = Lock()


def fingerprint(encoded: str) -> tuple[int, str]:
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid base64 image") from exc
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Thumbnail must be between 1 byte and 1 MiB")
    # Decode one image at a time on the light deployment. Do not accept vector/script formats.
    with _processing:
        try:
            with Image.open(io.BytesIO(raw), formats=["PNG", "JPEG"]) as image:
                if image.width * image.height > MAX_PIXELS or image.width > 4096 or image.height > 4096:
                    raise ValueError("Thumbnail exceeds the 1 megapixel limit")
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Animated images are not supported")
                image.load()
                with ImageOps.exif_transpose(image).convert("L") as gray:
                    low, high = gray.getextrema()
                    if high - low < 8:
                        raise ValueError("A blank thumbnail has no usable visual evidence")
                    with gray.resize((9, 8), Image.Resampling.BILINEAR) as resized:
                        pixels = list(resized.get_flattened_data())
                        bits = 0
                        for y in range(8):
                            for x in range(8):
                                bits = (bits << 1) | (pixels[y * 9 + x] > pixels[y * 9 + x + 1])
            return bits, hashlib.sha256(raw).hexdigest()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError("Invalid or oversized PNG/JPEG thumbnail") from exc


class ImageQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image_base64: str = Field(min_length=1, max_length=1_398_104)
    kind: VisualQueryKind = VisualQueryKind.FRAGMENT
    limit: int = Field(default=10, ge=1, le=30)
    minimum_similarity: float = Field(default=0.75, ge=0, le=1, allow_inf_nan=False)


class ImageIndexRequest(ImageQuery):
    provenance: LayerProvenance
    source_license: str = Field(min_length=1, max_length=500)
    rights_note: str = Field(min_length=1, max_length=2000)


class ThumbnailVisualProvider:
    def __init__(self, path: Path, max_entries: int = 10000):
        self.path, self.max_entries = path, max_entries
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS visual_index_schema(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO visual_index_schema VALUES(1);
                CREATE TABLE IF NOT EXISTS visual_fingerprints(
                  id TEXT PRIMARY KEY, kind TEXT, fingerprint TEXT, image_sha256 TEXT,
                  scope TEXT, payload TEXT, UNIQUE(scope,kind,image_sha256));
                CREATE TABLE IF NOT EXISTS visual_index_audit(
                  id TEXT, actor TEXT, payload TEXT);
            ''')
            connection.commit()

    def publish(self, request: ImageIndexRequest, *, actor: str) -> dict:
        self._kind(request.kind)
        bits, image_sha = fingerprint(request.image_base64)
        provenance = request.provenance.model_copy(deep=True)
        provenance.extraction_method = "thumbnail-difference-hash"
        provenance.model, provenance.confidence = MODEL, None
        provenance.source_text = None
        provenance.timestamp = datetime.now(UTC)
        scope = json.dumps(provenance.source.model_dump(mode="json"), sort_keys=True)
        payload = {"id": str(uuid4()), "kind": request.kind, "image_sha256": image_sha,
                   "provenance": provenance.model_dump(mode="json"), "source_license": request.source_license,
                   "rights_note": request.rights_note, "publisher": actor, "model": MODEL}
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT payload FROM visual_fingerprints WHERE scope=? AND kind=? AND image_sha256=?",
                                          (scope, request.kind, image_sha)).fetchone()
            if existing:
                return json.loads(existing[0])
            if connection.execute("SELECT count(*) FROM visual_fingerprints").fetchone()[0] >= self.max_entries:
                raise ValueError("Light visual index capacity reached")
            encoded = json.dumps(payload, ensure_ascii=False)
            connection.execute("INSERT INTO visual_fingerprints VALUES(?,?,?,?,?,?)",
                               (payload["id"], request.kind, f"{bits:016x}", image_sha, scope, encoded))
            connection.execute("INSERT INTO visual_index_audit VALUES(?,?,?)", (payload["id"], actor, encoded))
        return payload

    @staticmethod
    def _kind(kind: VisualQueryKind):
        if kind not in {VisualQueryKind.FRAGMENT, VisualQueryKind.ILLUSTRATION}:
            raise ValueError("This provider does not support handwriting or layout identification")

    def search_image(self, query: ImageQuery) -> list[dict]:
        self._kind(query.kind)
        bits, _ = fingerprint(query.image_base64)
        return self._matches(bits, query.kind, query.limit, query.minimum_similarity)

    def _matches(self, bits: int, kind: VisualQueryKind, limit: int, minimum: float) -> list[dict]:
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("SELECT id,fingerprint FROM visual_fingerprints WHERE kind=?", (kind,))
            def candidates():
                for identifier, value in rows:
                    similarity = 1 - (bits ^ int(value, 16)).bit_count() / 64
                    if similarity >= minimum:
                        yield similarity, identifier
            # Only retain the top descriptors and load their full source metadata afterward.
            top = heapq.nsmallest(limit, candidates(), key=lambda pair: (-pair[0], pair[1]))
            matches = []
            for similarity, identifier in top:
                item = json.loads(connection.execute("SELECT payload FROM visual_fingerprints WHERE id=?", (identifier,)).fetchone()[0])
                matches.append({"index_id": identifier, "similarity": similarity, "model": MODEL,
                                "relation": "candidate_similarity", "provenance": item["provenance"],
                                "source_license": item["source_license"], "rights_note": item["rights_note"]})
            return matches

    def search(self, query: VisualQuery) -> list[VisualMatch]:
        self._kind(query.kind)
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("SELECT fingerprint,payload FROM visual_fingerprints WHERE kind=? ORDER BY rowid DESC", (query.kind,))
            for value, payload in rows:
                anchor = LayerProvenance.model_validate(json.loads(payload)["provenance"]).source
                if anchor == query.source:
                    return [VisualMatch.model_validate(item) for item in self._matches(int(value, 16), query.kind, query.limit, 0.75)]
        raise ValueError("Source has no curated thumbnail in this visual index")
