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
                         pages=[Page(id='academy-page', sequence=1, image='https://example.org/page.png'),
                                Page(id='visual-source-page', sequence=2, folio_label='Synthetic visual source 2',
                                     image='https://example.org/visual-source.png',
                                     regions=[Region(id='visual-source-region')])]))
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

from app.citations import CitationTarget
from app.living import LayerKind, LivingLayer
from app.living_routes import layer_repository
from app.models import Region
from app.museum import EvidenceClass, Exhibition, MuseumObject
from app.museum_routes import museum_repository

repository.put(Manuscript(id='museum-browser',title='Synthetic museum QA fixture',pages=[
    Page(id='museum-page',sequence=1,image='https://example.org/page.png',regions=[Region(id='museum-drawing')])]))
museum_prov=LayerProvenance(source=SourceAnchor(manuscript_id='museum-browser',page_id='museum-page',region_id='museum-drawing'),
    extraction_method='manual',reviewer='fixture-reviewer',evidence=[CitationTarget(manuscript_id='museum-browser',page_id='museum-page',region_id='museum-drawing')])
museum_repository().append(MuseumObject(object_id='museum-browser-object',name='Synthetic museum object',description='Synthetic interpretive example',
    evidence_class=EvidenceClass.INTERPRETIVE,original_illustration_region='museum-drawing',interpretation_notes='Synthetic assumptions for QA only',provenance=museum_prov),actor='fixture-reviewer')
museum_repository().append(Exhibition(exhibition_id='museum-browser-exhibition',title='Synthetic museum exhibition',theme='engineering',
    description='QA fixture, not a historical claim',object_ids=['museum-browser-object'],provenance=museum_prov),actor='fixture-reviewer')
layer_repository().append(LivingLayer(kind=LayerKind.VERIFIED,state=ReviewState.VERIFIED,text='Synthetic verified corpus excerpt',language='en',provenance=prov),actor='fixture-reviewer')

import base64
import io

from PIL import Image

from app.visual_index import ImageIndexRequest
from app.visual_index_routes import visual_index

image = Image.new('L', (90,80))
image.putdata([255 if x % 20 < 10 else 0 for y in range(80) for x in range(90)])
output = io.BytesIO(); image.save(output, format='PNG')
Path('/tmp/visual-fixture.png').write_bytes(output.getvalue())
visual_prov = prov.model_copy(deep=True)
visual_prov.source.page_id = 'visual-source-page'
visual_prov.source.region_id = 'visual-source-region'
visual_prov.source.source_uri = 'https://example.org/visual-source.png'
visual_index().publish(ImageIndexRequest(image_base64=base64.b64encode(output.getvalue()).decode(),
 source_license='test-only', rights_note='Synthetic QA rights only', provenance=visual_prov), actor='fixture-reviewer')

from app.accounts import account_repository

account_repository().create('browser-owner',Role.ADMIN,'Browser QA fixture pass!',actor='fixture-bootstrap',bootstrap=True)

from app.scholarship import (
    BibliographicMetadata,
    VariantReading,
    Witness,
    WitnessKind,
    Work,
    scholarship_store,
)

scholarship_store.put_work(Work(id='browser-work', title='Synthetic comparison QA'), actor='fixture-reviewer')
for witness_id, manuscript_id in [('browser-witness-a','browser-fixture'), ('browser-witness-b','academy-browser')]:
    scholarship_store.put_witness(Witness(id=witness_id,work_id='browser-work',manuscript_id=manuscript_id,
        kind=WitnessKind.MANUSCRIPT,label=witness_id,bibliography=BibliographicMetadata(title='Synthetic QA witness')),
        actor='fixture-reviewer')
scholarship_store.put_variant(VariantReading(id='browser-variant',work_id='browser-work',locus='Synthetic comparison locus',
    readings={'browser-witness-a':'Synthetic original word','browser-witness-b':'Synthetic changed word'},
    sources=[CitationTarget(manuscript_id='academy-browser',page_id='visual-source-page',region_id='visual-source-region')]),
    actor='fixture-reviewer')
