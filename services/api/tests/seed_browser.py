import json
import sys
from pathlib import Path

sys.path.insert(0,'services/api')
from app.auth import Role, issue_token
from app.models import Manuscript, Page, Point, Region
from app.repository import repository

repository.put(Manuscript(id='browser-fixture',title='QA fixture',pages=[Page(id='browser-page',sequence=1,image='https://example.org/page.png',canvas_uri='https://example.org/canvas',regions=[Region(id='browser-region',polygon=[Point(x=1,y=1),Point(x=30,y=1),Point(x=30,y=40),Point(x=1,y=40)])])]))
Path('/tmp/browser-fixture.json').write_text(json.dumps({'token':issue_token('browser-editor',Role.TRANSCRIBER,ttl_seconds=600)}))

from app.academy_routes import academy_repository
from app.living import LayerProvenance, ReviewState, SourceAnchor
from app.ottoman import OttomanRecord, OttomanStage
from app.ottoman_academy import DictionaryEntry, ReadingExercise
from app.ottoman_routes import ottoman_repository

# Only synthetic QA fixtures; never represented as historical scholarship.
repository.put(Manuscript(id='academy-browser', title='Synthetic academy QA fixture', license='test-only',
                         pages=[Page(id='academy-page', sequence=1, image='https://example.org/page.png')]))
prov = LayerProvenance(source=SourceAnchor(manuscript_id='academy-browser', page_id='academy-page'),
                       extraction_method='manual', reviewer='fixture-reviewer')
original = OttomanRecord(stage=OttomanStage.TRANSCRIPTION, state=ReviewState.VERIFIED,
                         text='Synthetic original exercise', provenance=prov)
ottoman_repository().append(original, actor='fixture-reviewer')
latin = OttomanRecord(stage=OttomanStage.TRANSLITERATION, state=ReviewState.VERIFIED,
                      text='Synthetic Latin exercise', provenance=prov, input_revision_id=original.id)
ottoman_repository().append(latin, actor='fixture-reviewer')
academy_repository().put_exercise(ReadingExercise(title='Synthetic browser exercise',
    transcription_revision=original.id, transliteration_revision=latin.id,
    rights_note='Synthetic test fixture, not a historical document', source_license='test-only'),
    'academy-browser', 'academy-page', actor='fixture-reviewer')
academy_repository().append_entry(DictionaryEntry(entry_id='browser-fixture-word', spelling='Synthetic dictionary fixture',
    arabic='Synthetic meaning', provenance=prov), actor='fixture-editor')

from app.heritage_graph import EntityKind, HistoricalEntity, HistoricalInterval, HistoricalLocation
from app.heritage_routes import graph_repository

graph_repository().append(HistoricalEntity(entity_id='browser-heritage', name='Synthetic historical place',
    kind=EntityKind.PLACE, interval=HistoricalInterval(start_year=1000, end_year=1050),
    location=HistoricalLocation(latitude=20, longitude=30, label='Synthetic QA coordinates'),
    provenance=prov), actor='fixture-editor')
