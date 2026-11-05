import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "KisanVani" in data["app"]

def test_system_status_endpoint():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "stt_engine" in data
    assert "whisper" in data["stt_engine"]

def test_text_chat_endpoint_pink_bollworm():
    payload = {
        "query": "माझ्या कापसाच्या पिकावर गुलाबी बोंडअळी आली आहे, काय करावे?",
        "language": "mr",
        "crop_name": "Cotton",
        "include_audio": False
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "कापूस" in data["transcript"] or "कापसा" in data["transcript"]
    assert len(data["sources"]) > 0

def test_conversations_history_endpoint():
    response = client.get("/api/v1/conversations")
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert isinstance(data["conversations"], list)
