import os
from fastapi.testclient import TestClient

from main import app, build_storage_path


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_from_telegram_returns_storage_meta(tmp_path) -> None:
    payload = {
        "telegram_file_id": "file_123",
        "file_name": "invoice.pdf",
        "warehouse": "Алматы",
        "category": "Авто",
        "subcategory": "Ремонт",
        "author_id": 42,
    }
    response = client.post("/files/from-telegram", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "invoice.pdf"
    assert "/Авто/Ремонт/" in data["storage_path"]


def test_build_storage_path_structure() -> None:
    path = build_storage_path("Авто", "ГСМ", "check.png")
    assert path.startswith("/Авто/ГСМ/")
    assert path.endswith("check.png")


