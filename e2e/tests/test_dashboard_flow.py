"""
E2E Tests: Dashboard Flow

Tests the dashboard statistics endpoint against the running API.
"""

from datetime import datetime, timedelta, timezone

import pytest


class TestDashboardFlow:
    """E2E tests for dashboard statistics."""

    @pytest.mark.smoke
    def test_stats_endpoint_returns_correct_structure(self, http_client):
        """Test that the stats endpoint returns the expected structure."""
        # Act
        response = http_client.get("/api/v1/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

        stats = data["data"]
        assert "vehicle_count_by_status" in stats
        assert "driver_count_by_status" in stats
        assert "active_assignments_count" in stats
        assert "total_assignments_count" in stats

    def test_stats_reflect_created_vehicle(self, http_client, sample_vehicle_data):
        """Test that creating a vehicle updates the stats."""
        # Arrange: Get initial stats
        initial_response = http_client.get("/api/v1/stats")
        initial_stats = initial_response.json()["data"]
        initial_active = initial_stats["vehicle_count_by_status"].get("active", 0)

        # Act: Create a vehicle
        create_response = http_client.post("/api/v1/vehicles", json=sample_vehicle_data)
        vehicle_id = create_response.json()["data"]["id"]

        # Get updated stats
        updated_response = http_client.get("/api/v1/stats")
        updated_stats = updated_response.json()["data"]
        updated_active = updated_stats["vehicle_count_by_status"].get("active", 0)

        # Assert
        assert updated_active == initial_active + 1

        # Cleanup
        http_client.delete(f"/api/v1/vehicles/{vehicle_id}")

    def test_stats_reflect_created_driver(self, http_client, sample_driver_data):
        """Test that creating a driver updates the stats."""
        # Arrange: Get initial stats
        initial_response = http_client.get("/api/v1/stats")
        initial_stats = initial_response.json()["data"]
        initial_active = initial_stats["driver_count_by_status"].get("active", 0)

        # Act: Create a driver
        create_response = http_client.post("/api/v1/drivers", json=sample_driver_data)
        driver_id = create_response.json()["data"]["id"]

        # Get updated stats
        updated_response = http_client.get("/api/v1/stats")
        updated_stats = updated_response.json()["data"]
        updated_active = updated_stats["driver_count_by_status"].get("active", 0)

        # Assert
        assert updated_active == initial_active + 1

        # Cleanup
        http_client.delete(f"/api/v1/drivers/{driver_id}")

    def test_stats_reflect_active_assignment(
        self, http_client, created_driver, created_vehicle
    ):
        """Test that creating an assignment updates active assignment count."""
        # Arrange: Get initial stats
        initial_response = http_client.get("/api/v1/stats")
        initial_stats = initial_response.json()["data"]
        initial_active = initial_stats["active_assignments_count"]
        initial_total = initial_stats["total_assignments_count"]

        # Act: Create an assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Get updated stats
        updated_response = http_client.get("/api/v1/stats")
        updated_stats = updated_response.json()["data"]

        # Assert
        assert updated_stats["active_assignments_count"] == initial_active + 1
        assert updated_stats["total_assignments_count"] == initial_total + 1

        # Cleanup: Close the assignment
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")

    def test_stats_update_after_closing_assignment(
        self, http_client, created_driver, created_vehicle
    ):
        """Test that closing an assignment updates the active count."""
        # Arrange: Create an assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Get stats after creation
        after_create_response = http_client.get("/api/v1/stats")
        after_create_stats = after_create_response.json()["data"]
        active_after_create = after_create_stats["active_assignments_count"]

        # Act: Close the assignment
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")

        # Get stats after closing
        after_close_response = http_client.get("/api/v1/stats")
        after_close_stats = after_close_response.json()["data"]
        active_after_close = after_close_stats["active_assignments_count"]

        # Assert: Active count should decrease, total should stay same
        assert active_after_close == active_after_create - 1

    def test_health_endpoint(self, http_client):
        """Test the health endpoint returns healthy status."""
        # Act
        response = http_client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["database"] == "healthy"
