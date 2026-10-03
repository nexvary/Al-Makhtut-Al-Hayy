from __future__ import annotations

import json
from html import escape

from .citations import CitationTarget
from .models import Manuscript, TextLayerKind
from .scholarship import Witness


def scholarly_citation(target: CitationTarget, *, base_uri: str = "https://example.invalid") -> str:
    region = f"#region={target.region_id}" if target.region_id else ""
    return (
        f"{base_uri.rstrip('/')}/manuscripts/{target.manuscript_id}/pages/"
        f"{target.page_id}{region}"
    )


def tei_xml(manuscript: Manuscript) -> str:
    body: list[str] = []
    for page in sorted(manuscript.pages, key=lambda item: item.sequence):
        body.append(f'<pb n="{escape(page.folio_label or str(page.sequence))}" xml:id="{escape(page.id)}"/>')
        for region in sorted(page.regions, key=lambda item: item.reading_order or 0):
            text = next(
                (
                    layer.text
                    for layer in region.layers
                    if layer.kind == TextLayerKind.VERIFIED and layer.status == "verified"
                ),
                None,
            )
            if text:
                body.append(f'<lb xml:id="{escape(region.id)}"/>{escape(text)}')
    content = "\n".join(body)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt>"
        f"<title>{escape(manuscript.title)}</title>"
        "</titleStmt><publicationStmt><p>Exported by Al-Makhtut-Al-Hayy</p></publicationStmt>"
        "<sourceDesc><p>Source-traceable manuscript export.</p></sourceDesc></fileDesc></teiHeader>"
        f"<text><body>{content}</body></text></TEI>"
    )


def iiif_supplementing_annotation_page(manuscript: Manuscript, page_id: str) -> dict:
    page = next(page for page in manuscript.pages if page.id == page_id)
    canvas = page.canvas_uri or page.id
    items = []
    for region in page.regions:
        verified = next(
            (
                layer.text
                for layer in region.layers
                if layer.kind == TextLayerKind.VERIFIED and layer.status == "verified"
            ),
            None,
        )
        if not verified or not region.polygon:
            continue
        xs = [point.x for point in region.polygon]
        ys = [point.y for point in region.polygon]
        x, y = min(xs), min(ys)
        width, height = max(xs) - x, max(ys) - y
        items.append(
            {
                "id": f"{canvas}/annotations/{region.id}",
                "type": "Annotation",
                "motivation": "supplementing",
                "body": {"type": "TextualBody", "value": verified, "language": "ar"},
                "target": f"{canvas}#xywh={x:g},{y:g},{width:g},{height:g}",
            }
        )
    return {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": f"{canvas}/annotations/transcription",
        "type": "AnnotationPage",
        "items": items,
    }


def research_bundle(manuscript: Manuscript, witnesses: list[Witness] | None = None) -> str:
    payload = {
        "format": "al-makhtut-research-bundle/v1",
        "manuscript": manuscript.model_dump(mode="json"),
        "witnesses": [item.model_dump(mode="json") for item in (witnesses or [])],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
