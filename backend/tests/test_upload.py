from pathlib import Path

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_upload_saves_file(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))

    response = client.post(
        "/uploads",
        files={"file": ("sample.txt", b"hello garim", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "sample.txt"
    assert body["content_type"] == "text/plain"
    assert body["size"] == 11
    assert body["upload_id"]
    assert Path(body["stored_path"]).exists()
    assert Path(body["stored_path"]).read_bytes() == b"hello garim"


def test_meta_oauth_routes_are_not_registered():
    response = client.get("/oauth/meta/start")

    assert response.status_code == 404
