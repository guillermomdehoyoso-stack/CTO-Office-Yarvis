from fastapi.testclient import TestClient

from yarvis_api.main import app


def test_health_reports_only_api_process_availability():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "yarvis-api",
    }
