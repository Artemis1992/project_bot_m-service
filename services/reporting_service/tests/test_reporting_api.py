from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_append_request_returns_google_row_id() -> None:
    payload = {
        "request_id": 10,
        "goal": "Проинвестировать в оборудование",
        "item_name": "AI-92",
        "quantity": "1",
        "amount": 15000,
        "comment": "Комментарий",
        "status": "approved",
        "history": "2025-10-16T12:00 - утверждено",
    }
    response = client.post("/reports/requests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Строка добавлена в Google Sheets."
    assert "google_row_id" in data
