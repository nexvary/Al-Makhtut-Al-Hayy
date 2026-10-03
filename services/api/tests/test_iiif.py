from app.iiif import parse_manifest


def test_parse_iiif_v3() -> None:
    manifest = {
        "items": [
            {
                "id": "https://example.test/canvas/1",
                "label": {"ar": ["الورقة 1"]},
                "width": 1000,
                "height": 1500,
                "items": [
                    {
                        "items": [
                            {
                                "body": {
                                    "id": "https://example.test/image.jpg",
                                    "service": [{"id": "https://images.example.test/iiif/1"}],
                                }
                            }
                        ]
                    }
                ],
            }
        ]
    }
    pages = parse_manifest(manifest)
    assert pages[0].label == "الورقة 1"
    assert pages[0].image_service == "https://images.example.test/iiif/1"


def test_parse_iiif_v2() -> None:
    manifest = {
        "sequences": [
            {
                "canvases": [
                    {
                        "@id": "https://example.test/canvas/1",
                        "label": "f. 1r",
                        "images": [
                            {
                                "resource": {
                                    "@id": "https://example.test/image.jpg",
                                    "service": {"@id": "https://images.example.test/iiif/1"},
                                }
                            }
                        ],
                    }
                ]
            }
        ]
    }
    pages = parse_manifest(manifest)
    assert pages[0].id.endswith("/1")
