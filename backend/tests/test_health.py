"""
Integration tests for the health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the /api/v1/health endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """Test that health check returns 200 OK."""
        # Arrange & Act
        response = client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200

    def test_health_check_returns_success_true(self, client: TestClient):
        """Test that health check response has success=true."""
        # Arrange & Act
        response = client.get("/api/v1/health")
        data = response.json()

        # Assert
        assert data["success"] is True

    def test_health_check_returns_health_data(self, client: TestClient):
        """Test that health check returns health status data."""
        # Arrange & Act
        response = client.get("/api/v1/health")
        data = response.json()

        # Assert
        assert "data" in data
        assert "status" in data["data"]
        assert "version" in data["data"]
        assert "database" in data["data"]

    def test_health_check_returns_meta_with_request_id(self, client: TestClient):
        """Test that health check response includes meta with request_id."""
        # Arrange & Act
        response = client.get("/api/v1/health")
        data = response.json()

        # Assert
        assert "meta" in data
        assert "request_id" in data["meta"]
        assert "timestamp" in data["meta"]

    def test_health_check_returns_request_id_header(self, client: TestClient):
        """Test that health check response includes X-Request-ID header."""
        # Arrange & Act
        response = client.get("/api/v1/health")

        # Assert
        assert "X-Request-ID" in response.headers

    def test_health_check_returns_correlation_id_header(self, client: TestClient):
        """Test that health check response includes X-Correlation-ID header."""
        # Arrange & Act
        response = client.get("/api/v1/health")

        # Assert
        assert "X-Correlation-ID" in response.headers

    def test_health_check_preserves_correlation_id_from_request(
        self, client: TestClient
    ):
        """Test that provided correlation ID is preserved in response."""
        # Arrange
        correlation_id = "corr_test123456"

        # Act
        response = client.get(
            "/api/v1/health",
            headers={"X-Correlation-ID": correlation_id},
        )

        # Assert
        assert response.headers.get("X-Correlation-ID") == correlation_id
