from htr.alto import parse_alto_lines


def test_parse_alto_line() -> None:
    xml = """<?xml version="1.0"?>
    <alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
      <Layout><Page><PrintSpace><TextBlock>
        <TextLine ID="l1" HPOS="10" VPOS="20" WIDTH="100" HEIGHT="30">
          <String CONTENT="السلام" WC="0.9"/>
          <String CONTENT="عليكم" WC="0.8"/>
        </TextLine>
      </TextBlock></PrintSpace></Page></Layout>
    </alto>"""
    lines = parse_alto_lines(xml)
    assert lines[0].text == "السلام عليكم"
    assert lines[0].polygon[2].x == 110
    assert round(lines[0].confidence or 0, 2) == 0.85
