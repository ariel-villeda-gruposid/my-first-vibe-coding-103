"""
E2E Tests: Assignment Flow

Tests the complete assignment lifecycle against the running API.
"""

from datetime import datetime, timedelta, timezone

import pytest


class TestAssignmentFlow:
    """E2E tests for assignment operations."""

    @pytest.mark.smoke
    def test_create_assignment_flow(self, http_client, created_driver, created_vehicle):
        """Test creating a new assignment through the API."""
        # Arrange
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
            "notes": "E2E test assignment",
        }

        # Act: Create an assignment
        response = http_client.post("/api/v1/assignments", json=assignment_data)

        # Assert: Assignment created successfully
        assert response.status_code == 201, f"Failed: {response.text}"
        data = response.json()
        assert data["driver_id"] == created_driver["id"]
        assert data["vehicle_id"] == created_vehicle["id"]
        assert data["notes"] == "E2E test assignment"
        assert "id" in data

        # Cleanup: Close the assignment
        assignment_id = data["id"]
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")

    def test_get_assignment_by_id(self, http_client, created_driver, created_vehicle):
        """Test retrieving an assignment by ID."""
        # Arrange: Create an assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Act
        response = http_client.get(f"/api/v1/assignments/{assignment_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == assignment_id

        # Cleanup
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")

    def test_list_assignments(self, http_client, created_driver, created_vehicle):
        """Test listing assignments."""
        # Arrange: Create an assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Act
        response = http_client.get("/api/v1/assignments")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["pagination"]["total"] >= 1

        # Cleanup
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")

    def test_close_assignment_flow(self, http_client, created_driver, created_vehicle):
        """Test closing an active assignment."""
        # Arrange: Create an assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Act: Close the assignment
        close_response = http_client.post(f"/api/v1/assignments/{assignment_id}/close")

        # Assert
        assert close_response.status_code == 200
        data = close_response.json()
        assert data["end_datetime"] is not None

    def test_filter_active_assignments(
        self, http_client, created_driver, created_vehicle
    ):
        """Test filtering for active assignments only."""
        # Arrange: Create an assignment (active, open-ended)
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
            # No end_datetime - this is an active/ongoing assignment
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Act: Filter for active
        response = http_client.get("/api/v1/assignments?active=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] >= 1

        # Verify our created assignment is in the list
        assignment_ids = [a["id"] for a in data["data"]]
        assert assignment_id in assignment_ids

        # Cleanup
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")

    def test_cannot_create_overlapping_assignment_same_driver(
        self, http_client, created_driver, created_vehicle
    ):
        """Test that a driver cannot have overlapping assignments."""
        import uuid

        # Arrange: Create first assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        # Create a second vehicle for the second assignment
        unique_plate = f"OVL{uuid.uuid4().hex[:6].upper()}"
        second_vehicle_data = {
            "plate_number": unique_plate,
            "make": "SecondMake",
            "model": "SecondModel",
            "year": 2024,
            "type": "sedan",
            "fuel_type": "gasoline",
            "status": "active",
        }
        second_vehicle_response = http_client.post(
            "/api/v1/vehicles", json=second_vehicle_data
        )
        assert (
            second_vehicle_response.status_code == 201
        ), f"Failed to create second vehicle: {second_vehicle_response.text}"
        second_vehicle_id = second_vehicle_response.json()["data"]["id"]

        # Act: Try to create overlapping assignment for same driver
        overlapping_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": second_vehicle_id,
            "start_datetime": start_time.isoformat(),
        }
        overlap_response = http_client.post(
            "/api/v1/assignments", json=overlapping_data
        )

        # Assert: Should fail with conflict
        assert overlap_response.status_code == 409

        # Cleanup
        http_client.post(f"/api/v1/assignments/{assignment_id}/close")
        http_client.delete(f"/api/v1/vehicles/{second_vehicle_id}")

    def test_complete_assignment_lifecycle(
        self, http_client, created_driver, created_vehicle
    ):
        """Test the complete lifecycle: create -> update -> close."""
        # Step 1: Create assignment
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assignment_data = {
            "driver_id": created_driver["id"],
            "vehicle_id": created_vehicle["id"],
            "start_datetime": start_time.isoformat(),
            "notes": "Initial notes",
        }
        create_response = http_client.post("/api/v1/assignments", json=assignment_data)
        assert create_response.status_code == 201
        assignment_id = create_response.json()["id"]

        # Step 2: Update assignment notes
        update_response = http_client.patch(
            f"/api/v1/assignments/{assignment_id}",
            json={"notes": "Updated notes"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["notes"] == "Updated notes"

        # Step 3: Close assignment
        close_response = http_client.post(f"/api/v1/assignments/{assignment_id}/close")
        assert close_response.status_code == 200
        assert close_response.json()["end_datetime"] is not None

        # Step 4: Verify assignment is closed
        get_response = http_client.get(f"/api/v1/assignments/{assignment_id}")
        assert get_response.status_code == 200
        assert get_response.json()["end_datetime"] is not None
