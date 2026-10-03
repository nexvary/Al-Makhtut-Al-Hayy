from fastapi.testclient import TestClient

from app.auth import Role, issue_token
from app.main import app

client = TestClient(app)


def test_end_to_end_ingest_read_and_grounded_empty_answer() -> None:
    token = issue_token("admin-test", Role.ADMIN)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "manifest_url": "https://example.test/manifest",
        "title": "مخطوط تجريبي",
        "manifest": {
            "items": [
                {
                    "id": "https://example.test/canvas/1",
                    "width": 1000,
                    "height": 1400,
                    "items": [
                        {
                            "items": [
                                {
                                    "body": {
                                        "id": "https://example.test/image.jpg"
                                    }
                                }
                            ]
                        }
                    ],
                }
            ]
        },
    }
    imported = client.post("/api/v1/ingestion/iiif", json=payload, headers=headers)
    assert imported.status_code == 200
    manuscript_id = imported.json()["id"]

    fetched = client.get(f"/api/v1/manuscripts/{manuscript_id}")
    assert fetched.status_code == 200
    assert fetched.json()["pages"][0]["image_width"] == 1000

    answer = client.post("/api/v1/qa/ask", json={"question": "ما محتوى الصفحة؟"})
    assert answer.status_code == 200
    assert answer.json()["insufficient_evidence"] is True
