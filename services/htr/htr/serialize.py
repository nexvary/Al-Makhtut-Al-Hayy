from __future__ import annotations

from html import escape

from .contracts import RecognizedLine


def lines_to_alto(lines: list[RecognizedLine], width: int = 1, height: int = 1) -> str:
    chunks: list[str] = []
    for line in lines:
        xs = [point.x for point in line.polygon] or [0]
        ys = [point.y for point in line.polygon] or [0]
        x, y = min(xs), min(ys)
        w, h = max(xs) - x, max(ys) - y
        strings = "".join(
            f'<String CONTENT="{escape(word, quote=True)}"/>'
            for word in line.text.split()
        )
        chunks.append(
            f'<TextLine ID="{escape(line.id, quote=True)}" HPOS="{x:g}" VPOS="{y:g}" '
            f'WIDTH="{w:g}" HEIGHT="{h:g}">{strings}</TextLine>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout>'
        f'<Page WIDTH="{width}" HEIGHT="{height}"><PrintSpace><TextBlock>'
        + "".join(chunks)
        + "</TextBlock></PrintSpace></Page></Layout></alto>"
    )


def lines_to_pagexml(lines: list[RecognizedLine], width: int = 1, height: int = 1) -> str:
    chunks: list[str] = []
    for line in lines:
        points = " ".join(f"{point.x:g},{point.y:g}" for point in line.polygon)
        confidence = "" if line.confidence is None else f' conf="{line.confidence:g}"'
        chunks.append(
            f'<TextLine id="{escape(line.id, quote=True)}"><Coords points="{points}"/>'
            f"<TextEquiv{confidence}><Unicode>{escape(line.text)}</Unicode></TextEquiv></TextLine>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">'
        f'<Page imageWidth="{width}" imageHeight="{height}"><TextRegion id="r1">'
        + "".join(chunks)
        + "</TextRegion></Page></PcGts>"
    )
