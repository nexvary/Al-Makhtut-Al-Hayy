import base64
import io

import pytest
from PIL import Image

from app.living import LayerProvenance, SourceAnchor
from app.visual_index import ImageIndexRequest, ImageQuery, ThumbnailVisualProvider, fingerprint
from app.visual_search import VisualQueryKind


def thumbnail(reverse=False, size=(90,80)):
    image = Image.new("L", size)
    image.putdata([((255 if x % 20 < 10 else 0) if not reverse else (0 if x % 20 < 10 else 255))
                   for y in range(size[1]) for x in range(size[0])])
    output = io.BytesIO()
    image.save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode()


def request(image=None):
    return ImageIndexRequest(image_base64=image or thumbnail(), source_license="Synthetic license",
        rights_note="Synthetic rights attestation, not historical material",
        provenance=LayerProvenance(source=SourceAnchor(manuscript_id="visual-fixture", page_id="p1", source_uri="original.png"),
                                   extraction_method="curated-original"))


def test_persistent_search_idempotent_index_and_distinct_candidates(tmp_path):
    provider = ThumbnailVisualProvider(tmp_path / "index.sqlite3", max_entries=2)
    published = provider.publish(request(), actor="curator")
    assert provider.publish(request(), actor="curator")["id"] == published["id"]
    provider.publish(request(thumbnail(True)), actor="curator")
    result = ThumbnailVisualProvider(provider.path).search_image(ImageQuery(image_base64=thumbnail(), minimum_similarity=0.9))
    assert len(result) == 1 and result[0]["index_id"] == published["id"]
    assert result[0]["similarity"] == 1
    assert result[0]["provenance"]["confidence"] is None
    assert result[0]["relation"] == "candidate_similarity"
    with pytest.raises(ValueError, match="capacity"):
        third = request(); third.provenance.source.page_id = "p2"
        provider.publish(third, actor="curator")


def test_rejects_invalid_blank_large_and_unsupported_images(tmp_path):
    with pytest.raises(ValueError):
        fingerprint("not an image")
    image = Image.new("L", (10,10)); output = io.BytesIO(); image.save(output,format="PNG")
    with pytest.raises(ValueError, match="blank"):
        fingerprint(base64.b64encode(output.getvalue()).decode())
    with pytest.raises(ValueError, match="megapixel"):
        fingerprint(thumbnail(size=(1025,1025)))
    provider = ThumbnailVisualProvider(tmp_path / "index.sqlite3")
    with pytest.raises(ValueError, match="handwriting"):
        provider.search_image(ImageQuery(image_base64=thumbnail(),kind=VisualQueryKind.HANDWRITING))


def test_api_roles_rights_source_and_live_query(tmp_path):
    from fastapi.testclient import TestClient

    from app.auth import Role, issue_token
    from app.main import app
    from app.models import Manuscript, Page
    from app.repository import repository
    from app.visual_index_routes import visual_index

    store = ThumbnailVisualProvider(tmp_path / "index.sqlite3")
    app.dependency_overrides[visual_index] = lambda: store
    repository.put(Manuscript(id="visual-fixture", title="Synthetic visual QA", license="Synthetic license",
                             pages=[Page(id="p1",sequence=1,image="original.png")]))
    body = request().model_dump(mode="json")
    try:
        with TestClient(app) as client:
            assert client.post("/api/v1/visual-search/index",json=body).status_code == 401
            editor = {"Authorization":"Bearer "+issue_token("editor",Role.EDITOR)}
            assert client.post("/api/v1/visual-search/index",json=body,headers=editor).status_code == 403
            curator = {"Authorization":"Bearer "+issue_token("curator",Role.REVIEWER)}
            invalid = {**body,"source_license":"Unrecorded rights"}
            assert client.post("/api/v1/visual-search/index",json=invalid,headers=curator).status_code == 422
            assert client.post("/api/v1/visual-search/index",json=body,headers=curator).status_code == 200
            result = client.post("/api/v1/visual-search/query",json={"image_base64":thumbnail()})
            assert result.status_code == 200 and result.json()["matches"][0]["similarity"] == 1
            assert result.json()["matches"][0]["provenance"]["source"]["page_id"] == "p1"
    finally:
        app.dependency_overrides.pop(visual_index,None)
