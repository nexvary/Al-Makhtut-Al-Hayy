from htr.alto import parse_alto_lines
from htr.contracts import Point, RecognizedLine
from htr.pagexml import parse_pagexml_lines
from htr.serialize import lines_to_alto, lines_to_pagexml


def sample() -> list[RecognizedLine]:
    return [
        RecognizedLine(
            id="l1",
            polygon=[
                Point(x=10, y=20),
                Point(x=110, y=20),
                Point(x=110, y=50),
                Point(x=10, y=50),
            ],
            text="بسم الله",
            confidence=0.9,
        )
    ]


def test_alto_round_trip() -> None:
    parsed = parse_alto_lines(lines_to_alto(sample(), 200, 300))
    assert parsed[0].text == "بسم الله"


def test_page_round_trip() -> None:
    parsed = parse_pagexml_lines(lines_to_pagexml(sample(), 200, 300))
    assert parsed[0].text == "بسم الله"
    assert parsed[0].confidence == 0.9
