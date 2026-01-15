# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test l'endpoint /health"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_currencies():
    """Test l'endpoint /currencies"""
    response = client.get("/currencies")
    assert response.status_code == 200
    assert "available_currencies" in response.json()
    assert "USD" in response.json()["available_currencies"]

def test_convert_currency():
    """Test l'endpoint /convert"""
    test_data = {
        "amount": 100,
        "from_currency": "EUR",
        "to_currency": "USD"
    }
    response = client.post("/convert", json=test_data)
    assert response.status_code == 200
    assert "converted_amount" in response.json()
    assert "exchange_rate" in response.json()