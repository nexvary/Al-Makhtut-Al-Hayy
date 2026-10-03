from __future__ import annotations

from xml.etree import ElementTree as ET

from .contracts import Point, RecognizedLine


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_alto_lines(xml_text: str) -> list[RecognizedLine]:
    """Convert ALTO TextLine geometry/text into the internal HTR contract."""
    root = ET.fromstring(xml_text)
    lines: list[RecognizedLine] = []

    for index, element in enumerate(root.iter(), start=1):
        if _local(element.tag) != "TextLine":
            continue

        x = float(element.attrib.get("HPOS", "0"))
        y = float(element.attrib.get("VPOS", "0"))
        width = float(element.attrib.get("WIDTH", "0"))
        height = float(element.attrib.get("HEIGHT", "0"))

        words: list[str] = []
        confidences: list[float] = []
        for child in element.iter():
            if _local(child.tag) != "String":
                continue
            content = child.attrib.get("CONTENT")
            if content:
                words.append(content)
            wc = child.attrib.get("WC")
            if wc is not None:
                try:
                    confidences.append(float(wc))
                except ValueError:
                    pass

        confidence = sum(confidences) / len(confidences) if confidences else None
        lines.append(
            RecognizedLine(
                id=element.attrib.get("ID", f"line-{index}"),
                polygon=[
                    Point(x=x, y=y),
                    Point(x=x + width, y=y),
                    Point(x=x + width, y=y + height),
                    Point(x=x, y=y + height),
                ],
                text=" ".join(words),
                confidence=confidence,
            )
        )
    return lines
