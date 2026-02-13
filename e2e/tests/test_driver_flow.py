"""
E2E Tests: Driver Flow

Tests the complete driver CRUD flow against the running API.
"""

import pytest


class TestDriverFlow:
    """E2E tests for driver operations."""

    @pytest.mark.smoke
    def test_create_driver_flow(self, http_client, sample_driver_data):
        """Test creating a new driver through the API."""
        # Act: Create a driver
        response = http_client.post("/api/v1/drivers", json=sample_driver_data)

        # Assert: Driver created successfully
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == sample_driver_data["name"]
        assert data["data"]["license_number"] == sample_driver_data["license_number"]
        assert data["data"]["status"] == "active"
        assert "id" in data["data"]

        # Cleanup
        driver_id = data["data"]["id"]
        http_client.delete(f"/api/v1/drivers/{driver_id}")

    def test_get_driver_by_id(self, http_client, created_driver):
        """Test retrieving a driver by ID."""
        # Act
        response = http_client.get(f"/api/v1/drivers/{created_driver['id']}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == created_driver["id"]
        assert data["data"]["name"] == created_driver["name"]

    def test_list_drivers(self, http_client, created_driver):
        """Test listing drivers."""
        # Act
        response = http_client.get("/api/v1/drivers")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] >= 1

    def test_update_driver(self, http_client, created_driver):
        """Test updating a driver."""
        # Arrange
        update_data = {"name": "Updated Driver Name"}

        # Act
        response = http_client.patch(
            f"/api/v1/drivers/{created_driver['id']}",
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Driver Name"

    def test_filter_drivers_by_status(self, http_client, created_driver):
        """Test filtering drivers by status."""
        # Act
        response = http_client.get("/api/v1/drivers?status=active")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(d["status"] == "active" for d in data["data"])

    def test_delete_driver(self, http_client, sample_driver_data):
        """Test deleting a driver (soft delete)."""
        # Arrange: Create a driver to delete
        create_response = http_client.post("/api/v1/drivers", json=sample_driver_data)
        driver_id = create_response.json()["data"]["id"]

        # Act
        delete_response = http_client.delete(f"/api/v1/drivers/{driver_id}")

        # Assert: Soft delete returns 204
        assert delete_response.status_code == 204

        # Verify driver is not in active list (soft deleted)
        list_response = http_client.get("/api/v1/drivers")
        driver_ids = [d["id"] for d in list_response.json()["data"]]
        assert driver_id not in driver_ids

    def test_create_duplicate_license_fails(
        self, http_client, created_driver, sample_driver_data
    ):
        """Test that creating a driver with duplicate license number fails."""
        # Arrange: Use the same license as created_driver
        duplicate_data = sample_driver_data.copy()
        duplicate_data["license_number"] = created_driver["license_number"]
        duplicate_data["email"] = "different@test.com"

        # Act
        response = http_client.post("/api/v1/drivers", json=duplicate_data)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "DUPLICATE" in data["error"]["code"]

    def test_suspend_and_reactivate_driver(self, http_client, created_driver):
        """Test suspending and reactivating a driver."""
        driver_id = created_driver["id"]

        # Act: Suspend the driver
        suspend_response = http_client.patch(
            f"/api/v1/drivers/{driver_id}",
            json={"status": "suspended"},
        )

        # Assert suspended
        assert suspend_response.status_code == 200
        assert suspend_response.json()["data"]["status"] == "suspended"

        # Act: Reactivate the driver
        reactivate_response = http_client.patch(
            f"/api/v1/drivers/{driver_id}",
            json={"status": "active"},
        )

        # Assert reactivated
        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["data"]["status"] == "active"
