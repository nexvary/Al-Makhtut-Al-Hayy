from htr.pagexml import parse_pagexml_lines


def test_parse_pagexml() -> None:
    xml = """<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
      <Page><TextRegion><TextLine id="l1">
        <Coords points="10,20 110,20 110,50 10,50"/>
        <TextEquiv conf="0.91"><Unicode>بسم الله</Unicode></TextEquiv>
      </TextLine></TextRegion></Page>
    </PcGts>"""
    lines = parse_pagexml_lines(xml)
    assert lines[0].text == "بسم الله"
    assert lines[0].confidence == 0.91
    assert len(lines[0].polygon) == 4
