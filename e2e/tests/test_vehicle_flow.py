"""
E2E Tests: Vehicle Flow

Tests the complete vehicle CRUD flow against the running API.
"""

import pytest


class TestVehicleFlow:
    """E2E tests for vehicle operations."""

    @pytest.mark.smoke
    def test_create_vehicle_flow(self, http_client, sample_vehicle_data):
        """Test creating a new vehicle through the API."""
        # Act: Create a vehicle
        response = http_client.post("/api/v1/vehicles", json=sample_vehicle_data)

        # Assert: Vehicle created successfully
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["plate_number"] == sample_vehicle_data["plate_number"]
        assert data["data"]["status"] == "active"
        assert "id" in data["data"]

        # Cleanup
        vehicle_id = data["data"]["id"]
        http_client.delete(f"/api/v1/vehicles/{vehicle_id}")

    def test_get_vehicle_by_id(self, http_client, created_vehicle):
        """Test retrieving a vehicle by ID."""
        # Act
        response = http_client.get(f"/api/v1/vehicles/{created_vehicle['id']}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == created_vehicle["id"]
        assert data["data"]["plate_number"] == created_vehicle["plate_number"]

    def test_list_vehicles(self, http_client, created_vehicle):
        """Test listing vehicles."""
        # Act
        response = http_client.get("/api/v1/vehicles")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] >= 1

    def test_update_vehicle(self, http_client, created_vehicle):
        """Test updating a vehicle."""
        # Arrange
        update_data = {"model": "UpdatedModel"}

        # Act
        response = http_client.patch(
            f"/api/v1/vehicles/{created_vehicle['id']}",
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["model"] == "UpdatedModel"

    def test_filter_vehicles_by_status(self, http_client, created_vehicle):
        """Test filtering vehicles by status."""
        # Act
        response = http_client.get("/api/v1/vehicles?status=active")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(v["status"] == "active" for v in data["data"])

    def test_delete_vehicle(self, http_client, sample_vehicle_data):
        """Test deleting a vehicle (soft delete)."""
        # Arrange: Create a vehicle to delete
        create_response = http_client.post("/api/v1/vehicles", json=sample_vehicle_data)
        vehicle_id = create_response.json()["data"]["id"]

        # Act
        delete_response = http_client.delete(f"/api/v1/vehicles/{vehicle_id}")

        # Assert: Soft delete returns 204
        assert delete_response.status_code == 204

        # Verify vehicle is not in active list (soft deleted)
        list_response = http_client.get("/api/v1/vehicles")
        vehicle_ids = [v["id"] for v in list_response.json()["data"]]
        assert vehicle_id not in vehicle_ids

    def test_create_duplicate_plate_fails(
        self, http_client, created_vehicle, sample_vehicle_data
    ):
        """Test that creating a vehicle with duplicate plate number fails."""
        # Arrange: Use the same plate as created_vehicle
        duplicate_data = sample_vehicle_data.copy()
        duplicate_data["plate_number"] = created_vehicle["plate_number"]

        # Act
        response = http_client.post("/api/v1/vehicles", json=duplicate_data)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "DUPLICATE" in data["error"]["code"]
