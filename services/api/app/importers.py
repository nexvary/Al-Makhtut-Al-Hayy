from __future__ import annotations

import hashlib

from .iiif import parse_manifest
from .models import Manuscript, Page


def _stable_id(value: str, prefix: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def manuscript_from_iiif(
    manifest: dict,
    *,
    manifest_url: str,
    title: str,
    author: str | None = None,
    source_institution: str | None = None,
    rights: str | None = None,
) -> Manuscript:
    canvases = parse_manifest(manifest)
    pages = [
        Page(
            id=_stable_id(canvas.id, "page"),
            sequence=index,
            folio_label=canvas.label,
            image=(
                f"{canvas.image_service}/full/max/0/default.jpg"
                if canvas.image_service
                else str(canvas.image_url)
            ),
            canvas_uri=canvas.id,
            regions=[],
        )
        for index, canvas in enumerate(canvases, start=1)
    ]
    return Manuscript(
        id=_stable_id(manifest_url, "ms"),
        title=title,
        author=author,
        source_institution=source_institution,
        source_url=manifest_url,
        license=rights,
        pages=pages,
    )
