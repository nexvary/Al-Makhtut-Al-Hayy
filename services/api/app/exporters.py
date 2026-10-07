from __future__ import annotations

from .models import Manuscript, TextLayerKind


def verified_plain_text(manuscript: Manuscript) -> str:
    pages: list[str] = []
    for page in sorted(manuscript.pages, key=lambda item: item.sequence):
        lines: list[str] = []
        for region in sorted(page.regions, key=lambda item: item.reading_order or 0):
            verified = next(
                (
                    layer.text
                    for layer in region.layers
                    if layer.kind == TextLayerKind.VERIFIED and layer.status == "verified"
                ),
                None,
            )
            if verified:
                lines.append(verified)
        if lines:
            pages.append("\n".join(lines))
    return "\n\n".join(pages)
