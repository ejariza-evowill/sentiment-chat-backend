from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_user():
    response = client.get("/user")
    assert response.status_code == 200
    assert response.json() == {"username": "testuser"}

def test_get_chat():
    response = client.get("/chat")
    assert response.status_code == 200
    assert response.json() == {"chat": "This is a chat"}