from __future__ import annotations

from xml.etree import ElementTree as ET

from .contracts import Point, RecognizedLine


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _points(value: str) -> list[Point]:
    points: list[Point] = []
    for pair in value.split():
        x, y = pair.split(",", 1)
        points.append(Point(x=float(x), y=float(y)))
    return points


def parse_pagexml_lines(xml_text: str) -> list[RecognizedLine]:
    root = ET.fromstring(xml_text)
    result: list[RecognizedLine] = []
    for index, line in enumerate((e for e in root.iter() if _local(e.tag) == "TextLine"), start=1):
        polygon: list[Point] = []
        text = ""
        confidence: float | None = None

        for child in line:
            if _local(child.tag) == "Coords" and child.attrib.get("points"):
                polygon = _points(child.attrib["points"])
            if _local(child.tag) == "TextEquiv":
                conf = child.attrib.get("conf")
                if conf is not None:
                    try:
                        confidence = float(conf)
                    except ValueError:
                        pass
                for node in child.iter():
                    if _local(node.tag) == "Unicode" and node.text:
                        text = node.text
                        break

        result.append(
            RecognizedLine(
                id=line.attrib.get("id", f"line-{index}"),
                polygon=polygon,
                text=text,
                confidence=confidence,
            )
        )
    return result
