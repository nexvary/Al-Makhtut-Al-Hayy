import json
import sys
from pathlib import Path

sys.path.insert(0,'services/api')
from app.auth import Role, issue_token
from app.models import Manuscript, Page, Point, Region
from app.repository import repository

repository.put(Manuscript(id='browser-fixture',title='QA fixture',pages=[Page(id='browser-page',sequence=1,image='https://example.org/page.png',canvas_uri='https://example.org/canvas',regions=[Region(id='browser-region',polygon=[Point(x=1,y=1),Point(x=30,y=1),Point(x=30,y=40),Point(x=1,y=40)])])]))
Path('/tmp/browser-fixture.json').write_text(json.dumps({'token':issue_token('browser-editor',Role.TRANSCRIBER,ttl_seconds=600)}))
