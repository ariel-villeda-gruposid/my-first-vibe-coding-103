"""
Tests for the Statistics API endpoint.

Verifies GET /api/v1/stats endpoint behavior.
"""

from unittest.mock import MagicMock, patch

import pytest
from app.api.v1.endpoints.statistics import get_statistics_service, router
from app.core.dependencies import get_database
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def mock_statistics_service():
    """Create a mock statistics service."""
    return MagicMock()


@pytest.fixture
def app(mock_statistics_service):
    """Create a test FastAPI application."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")

    # Override the database dependency
    mock_db = MagicMock()
    test_app.dependency_overrides[get_database] = lambda: mock_db

    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestGetDashboardStats:
    """Tests for GET /api/v1/stats endpoint."""

    def test_returns_200_with_stats(self, client):
        """Returns 200 with statistics data."""
        # Arrange
        mock_stats = {
            "vehicle_count_by_status": {"active": 10, "inactive": 5},
            "driver_count_by_status": {"active": 15, "suspended": 3},
            "active_assignments_count": 8,
            "total_assignments_count": 100,
        }

        with patch(
            "app.api.v1.endpoints.statistics.get_statistics_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_dashboard_stats.return_value = mock_stats
            mock_get_service.return_value = mock_service

            # Act
            response = client.get("/api/v1/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["vehicle_count_by_status"] == {"active": 10, "inactive": 5}
        assert data["data"]["driver_count_by_status"] == {"active": 15, "suspended": 3}
        assert data["data"]["active_assignments_count"] == 8
        assert data["data"]["total_assignments_count"] == 100

    def test_returns_empty_counts_when_no_data(self, client):
        """Returns zero counts when no data exists."""
        # Arrange
        mock_stats = {
            "vehicle_count_by_status": {},
            "driver_count_by_status": {},
            "active_assignments_count": 0,
            "total_assignments_count": 0,
        }

        with patch(
            "app.api.v1.endpoints.statistics.get_statistics_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_dashboard_stats.return_value = mock_stats
            mock_get_service.return_value = mock_service

            # Act
            response = client.get("/api/v1/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["active_assignments_count"] == 0
        assert data["data"]["total_assignments_count"] == 0

    def test_response_structure(self, client):
        """Response has correct structure with meta information."""
        # Arrange
        mock_stats = {
            "vehicle_count_by_status": {"active": 1},
            "driver_count_by_status": {"active": 1},
            "active_assignments_count": 0,
            "total_assignments_count": 0,
        }

        with patch(
            "app.api.v1.endpoints.statistics.get_statistics_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_dashboard_stats.return_value = mock_stats
            mock_get_service.return_value = mock_service

            # Act
            response = client.get("/api/v1/stats")

        # Assert
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "meta" in data
        assert "timestamp" in data["meta"]

    def test_calls_service_method(self, client):
        """Calls the service's get_dashboard_stats method."""
        # Arrange
        with patch(
            "app.api.v1.endpoints.statistics.get_statistics_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_dashboard_stats.return_value = {
                "vehicle_count_by_status": {},
                "driver_count_by_status": {},
                "active_assignments_count": 0,
                "total_assignments_count": 0,
            }
            mock_get_service.return_value = mock_service

            # Act
            client.get("/api/v1/stats")

            # Assert
            mock_service.get_dashboard_stats.assert_called_once()
