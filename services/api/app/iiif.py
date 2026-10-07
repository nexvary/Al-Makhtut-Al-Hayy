from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class IiifManifestError(ValueError):
    pass


@dataclass(frozen=True)
class IiifCanvas:
    id: str
    label: str
    image_service: str | None
    image_url: str | None
    width: int | None = None
    height: int | None = None


def _label(value: Any, fallback: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("@value"), str):
            return value["@value"]
        for key in ("ar", "en", "none"):
            candidate = value.get(key)
            if isinstance(candidate, list) and candidate and isinstance(candidate[0], str):
                return candidate[0]
        for candidate in value.values():
            if isinstance(candidate, list) and candidate and isinstance(candidate[0], str):
                return candidate[0]
    return fallback


def _service_id(service: Any) -> str | None:
    if isinstance(service, list):
        service = service[0] if service else None
    if not isinstance(service, dict):
        return None
    value = service.get("id") or service.get("@id")
    return value.rstrip("/") if isinstance(value, str) else None


def parse_manifest(manifest: dict[str, Any]) -> list[IiifCanvas]:
    """Parse the image-bearing canvases of IIIF Presentation v2 or v3."""
    if isinstance(manifest.get("items"), list):
        canvases: list[IiifCanvas] = []
        for index, canvas in enumerate(manifest["items"], start=1):
            body = (((canvas.get("items") or [{}])[0].get("items") or [{}])[0].get("body") or {})
            service = _service_id(body.get("service"))
            image_url = body.get("id") if isinstance(body.get("id"), str) else None
            if not service and not image_url:
                continue
            canvases.append(
                IiifCanvas(
                    id=str(canvas.get("id") or f"canvas-{index}"),
                    label=_label(canvas.get("label"), f"Page {index}"),
                    image_service=service,
                    image_url=image_url,
                    width=canvas.get("width") if isinstance(canvas.get("width"), int) else None,
                    height=canvas.get("height") if isinstance(canvas.get("height"), int) else None,
                )
            )
        if canvases:
            return canvases

    sequences = manifest.get("sequences")
    if isinstance(sequences, list) and sequences:
        raw_canvases = sequences[0].get("canvases")
        if isinstance(raw_canvases, list):
            canvases = []
            for index, canvas in enumerate(raw_canvases, start=1):
                images = canvas.get("images") or []
                resource = images[0].get("resource") if images else {}
                resource = resource or {}
                service = _service_id(resource.get("service"))
                image_url = resource.get("@id") if isinstance(resource.get("@id"), str) else None
                if not service and not image_url:
                    continue
                canvases.append(
                    IiifCanvas(
                        id=str(canvas.get("@id") or f"canvas-{index}"),
                        label=_label(canvas.get("label"), f"Page {index}"),
                        image_service=service,
                        image_url=image_url,
                        width=canvas.get("width") if isinstance(canvas.get("width"), int) else None,
                        height=canvas.get("height") if isinstance(canvas.get("height"), int) else None,
                    )
                )
            if canvases:
                return canvases

    raise IiifManifestError("No usable image canvases were found")
