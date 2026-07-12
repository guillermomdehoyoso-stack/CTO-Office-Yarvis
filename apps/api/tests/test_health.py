from fastapi.testclient import TestClient

from yarvis_api import main


def test_health_returns_ok_when_database_is_connected(monkeypatch):
    monkeypatch.setattr(main, "check_database_connection", lambda database_url: None)

    response = TestClient(main.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "yarvis-api",
        "database": "ok",
    }


def test_health_returns_503_when_database_is_unavailable(monkeypatch):
    def fail(database_url):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main, "check_database_connection", fail)

    response = TestClient(main.app).get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "degraded",
        "service": "yarvis-api",
        "database": "unavailable",
    }
