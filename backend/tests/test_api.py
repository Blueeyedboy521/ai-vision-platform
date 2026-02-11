"""
API tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_cameras():
    """Test list cameras endpoint."""
    response = client.get("/api/v1/cameras")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_list_areas():
    """Test list areas endpoint."""
    response = client.get("/api/v1/areas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_algorithms():
    """Test list algorithms endpoint."""
    response = client.get("/api/v1/algorithms")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_get_alarm_stats():
    """Test get alarm stats endpoint."""
    response = client.get("/api/v1/alarms/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "pending" in data


def test_get_system_info():
    """Test get system info endpoint."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "cpu_usage" in data


def test_login_success():
    """Test login with correct credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure():
    """Test login with wrong credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401
