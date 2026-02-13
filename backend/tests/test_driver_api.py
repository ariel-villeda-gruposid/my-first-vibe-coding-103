"""
API endpoint tests for Driver endpoints.

Tests the REST API behavior for driver operations using FastAPI dependency overrides.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from app.api.v1.endpoints.drivers import get_driver_service
from app.core.exceptions import (
    ConcurrencyException,
    ConflictException,
    NotFoundException,
)
from app.domain.models.driver import Driver, DriverStatus
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def sample_driver():
    """Creates a sample Driver for testing."""
    return Driver(
        name="John Doe",
        license_number="DL12345",
        contact_number="+1-555-123-4567",
        status=DriverStatus.ACTIVE,
    )


@pytest.fixture
def mock_service():
    """Creates a mock DriverService."""
    return MagicMock()


@pytest.fixture
def client_with_mock(mock_service):
    """
    Creates a test client with mocked driver service.

    Yields the client and mock service for test assertions.
    """
    app.dependency_overrides[get_driver_service] = lambda: mock_service
    yield TestClient(app), mock_service
    app.dependency_overrides.clear()


class TestListDrivers:
    """Tests for GET /api/v1/drivers endpoint."""

    def test_list_drivers_returns_empty_list(self, client_with_mock):
        """Returns empty list when no drivers exist."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_drivers.return_value = ([], 0)

        # Act
        response = client.get("/api/v1/drivers")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_drivers_returns_drivers(self, client_with_mock, sample_driver):
        """Returns list of drivers."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_drivers.return_value = ([sample_driver], 1)

        # Act
        response = client.get("/api/v1/drivers")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "John Doe"
        assert data["data"][0]["license_number"] == "DL12345"
        assert data["pagination"]["total"] == 1

    def test_list_drivers_with_filters(self, client_with_mock):
        """Passes filter parameters to service."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_drivers.return_value = ([], 0)

        # Act
        response = client.get(
            "/api/v1/drivers",
            params={
                "status": "suspended",
                "limit": 25,
                "skip": 10,
            },
        )

        # Assert
        assert response.status_code == 200
        mock_service.get_all_drivers.assert_called_once_with(
            status=DriverStatus.SUSPENDED,
            include_deleted=False,
            limit=25,
            skip=10,
            sort_by="updated_at",
            sort_order="desc",
        )


class TestListActiveDrivers:
    """Tests for GET /api/v1/drivers/active endpoint."""

    def test_list_active_drivers(self, client_with_mock, sample_driver):
        """Returns list of active drivers."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_active_drivers.return_value = ([sample_driver], 1)

        # Act
        response = client.get("/api/v1/drivers/active")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "active"


class TestGetDriverStats:
    """Tests for GET /api/v1/drivers/stats/by-status endpoint."""

    def test_get_driver_stats(self, client_with_mock):
        """Returns driver counts by status."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_driver_counts_by_status.return_value = {
            "active": 10,
            "suspended": 2,
        }

        # Act
        response = client.get("/api/v1/drivers/stats/by-status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["active"] == 10
        assert data["data"]["suspended"] == 2


class TestGetDriver:
    """Tests for GET /api/v1/drivers/{driver_id} endpoint."""

    def test_get_driver_returns_driver(self, client_with_mock, sample_driver):
        """Returns driver when found."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_driver_by_id.return_value = sample_driver
        mock_service.get_driver_etag.return_value = "abc123etag"

        # Act
        response = client.get(f"/api/v1/drivers/{sample_driver.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sample_driver.id
        assert data["data"]["name"] == "John Doe"
        assert response.headers.get("ETag") == "abc123etag"

    def test_get_driver_not_found(self, client_with_mock):
        """Returns 404 when driver not found."""
        # Arrange
        client, mock_service = client_with_mock
        driver_id = str(uuid.uuid4())
        mock_service.get_driver_by_id.side_effect = NotFoundException(
            code="DRIVER_NOT_FOUND",
            message=f"Driver with ID '{driver_id}' not found.",
        )

        # Act
        response = client.get(f"/api/v1/drivers/{driver_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DRIVER_NOT_FOUND"


class TestCreateDriver:
    """Tests for POST /api/v1/drivers endpoint."""

    def test_create_driver_success(self, client_with_mock, sample_driver):
        """Successfully creates a driver."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.create_driver.return_value = sample_driver
        mock_service.get_driver_etag.return_value = "new-etag"

        # Act
        response = client.post(
            "/api/v1/drivers",
            json={
                "name": "John Doe",
                "license_number": "DL12345",
                "contact_number": "+1-555-123-4567",
                "status": "active",
            },
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "John Doe"
        assert "Location" in response.headers
        assert response.headers.get("ETag") == "new-etag"

    def test_create_driver_duplicate_license(self, client_with_mock):
        """Returns 409 when license number already exists."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.create_driver.side_effect = ConflictException(
            code="DUPLICATE_LICENSE",
            message="A driver with license number 'DL12345' already exists.",
        )

        # Act
        response = client.post(
            "/api/v1/drivers",
            json={
                "name": "New Driver",
                "license_number": "DL12345",
                "contact_number": "555-1234",
            },
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DUPLICATE_LICENSE"

    def test_create_driver_validation_error(self, client_with_mock):
        """Returns 422 for invalid input."""
        # Arrange
        client, mock_service = client_with_mock

        # Act
        response = client.post(
            "/api/v1/drivers",
            json={
                "name": "",  # Empty name
                "license_number": "ABC-123",  # Invalid characters
                "contact_number": "12",  # Too short
            },
        )

        # Assert
        assert response.status_code == 422


class TestUpdateDriver:
    """Tests for PUT /api/v1/drivers/{driver_id} endpoint."""

    def test_update_driver_success(self, client_with_mock, sample_driver):
        """Successfully updates a driver."""
        # Arrange
        client, mock_service = client_with_mock
        updated_driver = Driver(
            id=sample_driver.id,
            name="Updated Name",
            license_number="UPD001",
            contact_number="555-9999",
            status=DriverStatus.ACTIVE,
        )
        mock_service.update_driver.return_value = updated_driver
        mock_service.get_driver_etag.return_value = "updated-etag"

        # Act
        response = client.put(
            f"/api/v1/drivers/{sample_driver.id}",
            json={
                "name": "Updated Name",
                "license_number": "UPD001",
                "contact_number": "555-9999",
                "status": "active",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Name"

    def test_update_driver_not_found(self, client_with_mock):
        """Returns 404 when driver doesn't exist."""
        # Arrange
        client, mock_service = client_with_mock
        driver_id = str(uuid.uuid4())
        mock_service.update_driver.side_effect = NotFoundException(
            code="DRIVER_NOT_FOUND",
            message=f"Driver with ID '{driver_id}' not found.",
        )

        # Act
        response = client.put(
            f"/api/v1/drivers/{driver_id}",
            json={
                "name": "Updated",
                "license_number": "LIC001",
                "contact_number": "555-1234",
                "status": "active",
            },
        )

        # Assert
        assert response.status_code == 404

    def test_update_driver_concurrency_conflict(self, client_with_mock, sample_driver):
        """Returns 412 when ETag doesn't match."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.update_driver.side_effect = ConcurrencyException()

        # Act
        response = client.put(
            f"/api/v1/drivers/{sample_driver.id}",
            json={
                "name": "Updated",
                "license_number": "LIC001",
                "contact_number": "555-1234",
                "status": "active",
            },
            headers={"If-Match": "wrong-etag"},
        )

        # Assert
        assert response.status_code == 412


class TestPatchDriver:
    """Tests for PATCH /api/v1/drivers/{driver_id} endpoint."""

    def test_patch_driver_single_field(self, client_with_mock, sample_driver):
        """Successfully patches a single field."""
        # Arrange
        client, mock_service = client_with_mock
        patched_driver = Driver(
            id=sample_driver.id,
            name="Patched Name",
            license_number=sample_driver.license_number,
            contact_number=sample_driver.contact_number,
            status=sample_driver.status,
        )
        mock_service.patch_driver.return_value = patched_driver
        mock_service.get_driver_etag.return_value = "patched-etag"

        # Act
        response = client.patch(
            f"/api/v1/drivers/{sample_driver.id}",
            json={"name": "Patched Name"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Patched Name"

    def test_patch_driver_status_change(self, client_with_mock, sample_driver):
        """Successfully patches driver status."""
        # Arrange
        client, mock_service = client_with_mock
        suspended_driver = Driver(
            id=sample_driver.id,
            name=sample_driver.name,
            license_number=sample_driver.license_number,
            contact_number=sample_driver.contact_number,
            status=DriverStatus.SUSPENDED,
        )
        mock_service.patch_driver.return_value = suspended_driver
        mock_service.get_driver_etag.return_value = "suspended-etag"

        # Act
        response = client.patch(
            f"/api/v1/drivers/{sample_driver.id}",
            json={"status": "suspended"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "suspended"

    def test_patch_driver_with_active_assignments_fails(
        self, client_with_mock, sample_driver
    ):
        """Returns 409 when suspending driver with active assignments."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.patch_driver.side_effect = ConflictException(
            code="DRIVER_HAS_ACTIVE_ASSIGNMENTS",
            message="Cannot change status to suspended while driver has active assignments.",
        )

        # Act
        response = client.patch(
            f"/api/v1/drivers/{sample_driver.id}",
            json={"status": "suspended"},
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DRIVER_HAS_ACTIVE_ASSIGNMENTS"


class TestDeleteDriver:
    """Tests for DELETE /api/v1/drivers/{driver_id} endpoint."""

    def test_delete_driver_success(self, client_with_mock, sample_driver):
        """Successfully deletes a driver."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.delete_driver.return_value = None

        # Act
        response = client.delete(f"/api/v1/drivers/{sample_driver.id}")

        # Assert
        assert response.status_code == 204

    def test_delete_driver_not_found(self, client_with_mock):
        """Returns 404 when driver doesn't exist."""
        # Arrange
        client, mock_service = client_with_mock
        driver_id = str(uuid.uuid4())
        mock_service.delete_driver.side_effect = NotFoundException(
            code="DRIVER_NOT_FOUND",
            message=f"Driver with ID '{driver_id}' not found.",
        )

        # Act
        response = client.delete(f"/api/v1/drivers/{driver_id}")

        # Assert
        assert response.status_code == 404

    def test_delete_driver_with_active_assignments(
        self, client_with_mock, sample_driver
    ):
        """Returns 409 when driver has active assignments."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.delete_driver.side_effect = ConflictException(
            code="DRIVER_HAS_ACTIVE_ASSIGNMENTS",
            message="Cannot delete driver with active assignments.",
        )

        # Act
        response = client.delete(f"/api/v1/drivers/{sample_driver.id}")

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DRIVER_HAS_ACTIVE_ASSIGNMENTS"


class TestPaginationFormat:
    """Tests for pagination response format."""

    def test_pagination_has_more_true(self, client_with_mock, sample_driver):
        """Pagination shows has_more when more results exist."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_drivers.return_value = ([sample_driver], 10)

        # Act
        response = client.get("/api/v1/drivers", params={"limit": 1, "skip": 0})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["has_more"] is True
        assert data["pagination"]["total"] == 10

    def test_pagination_has_more_false(self, client_with_mock, sample_driver):
        """Pagination shows has_more false when no more results."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_drivers.return_value = ([sample_driver], 1)

        # Act
        response = client.get("/api/v1/drivers", params={"limit": 50, "skip": 0})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["has_more"] is False
