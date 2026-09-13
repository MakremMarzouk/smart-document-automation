from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to Smart Document Automation API"
    }


def test_openapi_documentation_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    openapi_data = response.json()

    assert "/upload/auto" in openapi_data["paths"]
    assert "/upload/auto-background" in openapi_data["paths"]
    assert "/documents/queue/review" in openapi_data["paths"]