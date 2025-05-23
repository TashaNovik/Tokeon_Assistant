import pytest
from fastapi.testclient import TestClient
from tokeon_assistant_rest_api.main import create_app, configure_logging

def test_configure_logging_does_not_raise():
    configure_logging()

def test_create_app_returns_fastapi():
    app = create_app()
    assert app.title == "Tokeon Assistant REST API"
    assert app.version == "1.0.0"
    assert any(route.path == "/health" for route in app.routes)

def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"} 