"""
Pytest configuration and shared fixtures.
"""

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """
    Provides a test client for API integration tests.

    Returns:
        TestClient instance configured for the application.
    """
    return TestClient(app)


@pytest.fixture
def mock_settings(monkeypatch):
    """
    Provides mocked application settings for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Function to set environment variables.
    """

    def _set_env(key: str, value: str):
        monkeypatch.setenv(key, value)

    return _set_env
