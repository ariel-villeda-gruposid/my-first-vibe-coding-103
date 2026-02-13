"""
E2E Test Configuration and Fixtures.

Provides shared configuration and fixtures for end-to-end tests.
"""

import os
import uuid

import httpx
import pytest

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def api_base_url():
    """Return the API base URL."""
    return API_BASE_URL


@pytest.fixture(scope="session")
def frontend_url():
    """Return the frontend URL."""
    return FRONTEND_URL


@pytest.fixture(scope="session")
def http_client():
    """Create an HTTP client for API requests."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def unique_plate():
    """Generate a unique vehicle plate number."""
    return f"E2E{uuid.uuid4().hex[:6].upper()}"


@pytest.fixture
def unique_license():
    """Generate a unique driver license number."""
    return f"LIC{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def unique_email():
    """Generate a unique email address."""
    return f"e2e_{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture
def sample_vehicle_data(unique_plate):
    """Return sample vehicle data for creating a vehicle."""
    return {
        "plate_number": unique_plate,
        "make": "TestMake",
        "model": "TestModel",
        "year": 2024,
        "type": "sedan",
        "fuel_type": "gasoline",
        "status": "active",
    }


@pytest.fixture
def sample_driver_data(unique_license, unique_email):
    """Return sample driver data for creating a driver."""
    return {
        "name": "E2E Test Driver",
        "license_number": unique_license,
        "contact_number": "+1234567890",
        "email": unique_email,
        "status": "active",
    }


@pytest.fixture
def created_vehicle(http_client, sample_vehicle_data):
    """Create a vehicle and return its data. Clean up after test."""
    response = http_client.post("/api/v1/vehicles", json=sample_vehicle_data)
    assert response.status_code == 201, f"Failed to create vehicle: {response.text}"
    data = response.json()["data"]

    yield data

    # Cleanup: delete the vehicle
    http_client.delete(f"/api/v1/vehicles/{data['id']}")


@pytest.fixture
def created_driver(http_client, sample_driver_data):
    """Create a driver and return its data. Clean up after test."""
    response = http_client.post("/api/v1/drivers", json=sample_driver_data)
    assert response.status_code == 201, f"Failed to create driver: {response.text}"
    data = response.json()["data"]

    yield data

    # Cleanup: delete the driver
    http_client.delete(f"/api/v1/drivers/{data['id']}")
