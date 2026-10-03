from app.importers import manuscript_from_iiif
from app.offline import make_offline_pack


def test_import_and_offline_pack() -> None:
    manifest = {
        "items": [
            {
                "id": "https://example.test/canvas/1",
                "items": [{"items": [{"body": {"id": "https://example.test/1.jpg"}}]}],
            }
        ]
    }
    manuscript = manuscript_from_iiif(
        manifest,
        manifest_url="https://example.test/manifest",
        title="Test",
    )
    assert manuscript.pages[0].canvas_uri == "https://example.test/canvas/1"
    pack = make_offline_pack(manuscript)
    assert not pack.includes_images
