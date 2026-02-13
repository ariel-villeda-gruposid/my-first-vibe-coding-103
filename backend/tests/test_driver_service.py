"""
Unit tests for DriverService.

Tests business logic and service layer functionality.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from app.core.exceptions import (
    ConcurrencyException,
    ConflictException,
    NotFoundException,
)
from app.domain.models.driver import Driver, DriverStatus
from app.domain.services.driver_service import DriverService


@pytest.fixture
def mock_driver_repository():
    """Creates a mock DriverRepository."""
    return MagicMock()


@pytest.fixture
def driver_service(mock_driver_repository):
    """Creates a DriverService instance with mocked repository."""
    return DriverService(driver_repository=mock_driver_repository)


@pytest.fixture
def sample_driver():
    """Creates a sample Driver for testing."""
    return Driver(
        name="John Doe",
        license_number="DL12345",
        contact_number="+1-555-123-4567",
        status=DriverStatus.ACTIVE,
    )


class TestGetDriverById:
    """Tests for get_driver_by_id method."""

    def test_get_driver_by_id_returns_driver(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Returns driver when found."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver

        # Act
        result = driver_service.get_driver_by_id(sample_driver.id)

        # Assert
        assert result == sample_driver
        mock_driver_repository.find_by_id.assert_called_once_with(sample_driver.id)

    def test_get_driver_by_id_raises_not_found(
        self, driver_service, mock_driver_repository
    ):
        """Raises NotFoundException when driver not found."""
        # Arrange
        driver_id = str(uuid.uuid4())
        mock_driver_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            driver_service.get_driver_by_id(driver_id)

        assert exc_info.value.code == "DRIVER_NOT_FOUND"
        assert driver_id in exc_info.value.message


class TestGetAllDrivers:
    """Tests for get_all_drivers method."""

    def test_get_all_drivers_returns_list(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Returns list of drivers with total count."""
        # Arrange
        drivers = [sample_driver]
        mock_driver_repository.find_all.return_value = (drivers, 1)

        # Act
        result, total = driver_service.get_all_drivers()

        # Assert
        assert len(result) == 1
        assert result[0] == sample_driver
        assert total == 1

    def test_get_all_drivers_with_filters(self, driver_service, mock_driver_repository):
        """Passes filters to repository."""
        # Arrange
        mock_driver_repository.find_all.return_value = ([], 0)

        # Act
        driver_service.get_all_drivers(
            status=DriverStatus.SUSPENDED,
            include_deleted=True,
            limit=25,
            skip=10,
        )

        # Assert
        mock_driver_repository.find_all.assert_called_once_with(
            status=DriverStatus.SUSPENDED,
            include_deleted=True,
            limit=25,
            skip=10,
            sort_by="updated_at",
            sort_order="desc",
        )


class TestCreateDriver:
    """Tests for create_driver method."""

    def test_create_driver_success(self, driver_service, mock_driver_repository):
        """Successfully creates a new driver."""
        # Arrange
        mock_driver_repository.find_by_license_number.return_value = None
        mock_driver_repository.create.side_effect = lambda d: d

        # Act
        result = driver_service.create_driver(
            name="New Driver",
            license_number="NEW001",
            contact_number="555-1234",
            status=DriverStatus.ACTIVE,
        )

        # Assert
        assert result.name == "New Driver"
        assert result.license_number == "NEW001"
        mock_driver_repository.create.assert_called_once()

    def test_create_driver_duplicate_license_raises_conflict(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Raises ConflictException when license number already exists."""
        # Arrange
        mock_driver_repository.find_by_license_number.return_value = sample_driver

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            driver_service.create_driver(
                name="Duplicate Driver",
                license_number=sample_driver.license_number,
                contact_number="555-9999",
            )

        assert exc_info.value.code == "DUPLICATE_LICENSE"

    def test_create_driver_restores_deleted_driver(
        self, driver_service, mock_driver_repository
    ):
        """Restores soft-deleted driver when creating with same license."""
        # Arrange
        deleted_driver = Driver(
            name="Old Driver",
            license_number="DEL001",
            contact_number="555-0000",
            status=DriverStatus.ACTIVE,
        )
        deleted_driver.soft_delete()
        mock_driver_repository.find_by_license_number.return_value = deleted_driver
        mock_driver_repository.update.side_effect = lambda d: d

        # Act
        result = driver_service.create_driver(
            name="Restored Driver",
            license_number="DEL001",
            contact_number="555-9999",
            status=DriverStatus.ACTIVE,
        )

        # Assert
        assert result.name == "Restored Driver"
        assert result.deleted_at is None
        mock_driver_repository.update.assert_called_once()
        mock_driver_repository.create.assert_not_called()


class TestUpdateDriver:
    """Tests for update_driver method."""

    def test_update_driver_success(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Successfully updates a driver."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        mock_driver_repository.exists_by_license_number.return_value = False
        mock_driver_repository.update.side_effect = lambda d: d

        # Act
        result = driver_service.update_driver(
            driver_id=sample_driver.id,
            name="Updated Name",
            license_number="UPD001",
            contact_number="555-5555",
            status=DriverStatus.ACTIVE,
        )

        # Assert
        assert result.name == "Updated Name"
        mock_driver_repository.update.assert_called_once()

    def test_update_driver_not_found(self, driver_service, mock_driver_repository):
        """Raises NotFoundException when driver doesn't exist."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException):
            driver_service.update_driver(
                driver_id=str(uuid.uuid4()),
                name="Name",
                license_number="LIC001",
                contact_number="555-1234",
                status=DriverStatus.ACTIVE,
            )

    def test_update_driver_duplicate_license_raises_conflict(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Raises ConflictException when license conflicts with another driver."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        mock_driver_repository.exists_by_license_number.return_value = True

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            driver_service.update_driver(
                driver_id=sample_driver.id,
                name="Updated",
                license_number="CONFLICT001",
                contact_number="555-1234",
                status=DriverStatus.ACTIVE,
            )

        assert exc_info.value.code == "DUPLICATE_LICENSE"

    def test_update_driver_etag_mismatch_raises_concurrency(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Raises ConcurrencyException when ETag doesn't match."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        mock_driver_repository.generate_etag.return_value = "correct-etag"

        # Act & Assert
        with pytest.raises(ConcurrencyException):
            driver_service.update_driver(
                driver_id=sample_driver.id,
                name="Updated",
                license_number=sample_driver.license_number,
                contact_number="555-1234",
                status=DriverStatus.ACTIVE,
                etag="wrong-etag",
            )

    def test_update_driver_deleted_raises_not_found(
        self, driver_service, mock_driver_repository
    ):
        """Raises NotFoundException when updating a deleted driver."""
        # Arrange
        deleted_driver = Driver(
            name="Deleted",
            license_number="DEL002",
            contact_number="555-0000",
        )
        deleted_driver.soft_delete()
        mock_driver_repository.find_by_id.return_value = deleted_driver

        # Act & Assert
        with pytest.raises(NotFoundException):
            driver_service.update_driver(
                driver_id=deleted_driver.id,
                name="Updated",
                license_number="DEL002",
                contact_number="555-1234",
                status=DriverStatus.ACTIVE,
            )


class TestPatchDriver:
    """Tests for patch_driver method."""

    def test_patch_driver_single_field(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Patches only the provided field."""
        # Arrange
        original_name = sample_driver.name
        mock_driver_repository.find_by_id.return_value = sample_driver
        mock_driver_repository.update.side_effect = lambda d: d

        # Act
        result = driver_service.patch_driver(
            driver_id=sample_driver.id,
            contact_number="555-9999",
        )

        # Assert
        assert result.contact_number == "555-9999"
        mock_driver_repository.update.assert_called_once()

    def test_patch_driver_status_to_suspended_with_assignments(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Fails to suspend driver with active assignments."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        service_with_assignments = DriverService(
            driver_repository=mock_driver_repository,
            assignment_repository=MagicMock(),
        )
        # Mock that driver has active assignments
        with patch.object(
            service_with_assignments, "_has_active_assignments", return_value=True
        ):
            # Act & Assert
            with pytest.raises(ConflictException) as exc_info:
                service_with_assignments.patch_driver(
                    driver_id=sample_driver.id,
                    status=DriverStatus.SUSPENDED,
                )

            assert exc_info.value.code == "DRIVER_HAS_ACTIVE_ASSIGNMENTS"


class TestDeleteDriver:
    """Tests for delete_driver method."""

    def test_delete_driver_success(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Successfully soft deletes a driver."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        mock_driver_repository.soft_delete.return_value = True

        # Act
        driver_service.delete_driver(sample_driver.id)

        # Assert
        mock_driver_repository.soft_delete.assert_called_once_with(sample_driver.id)

    def test_delete_driver_not_found(self, driver_service, mock_driver_repository):
        """Raises NotFoundException when driver doesn't exist."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException):
            driver_service.delete_driver(str(uuid.uuid4()))

    def test_delete_driver_with_active_assignments(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Fails to delete driver with active assignments."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        service_with_assignments = DriverService(
            driver_repository=mock_driver_repository,
            assignment_repository=MagicMock(),
        )
        with patch.object(
            service_with_assignments, "_has_active_assignments", return_value=True
        ):
            # Act & Assert
            with pytest.raises(ConflictException) as exc_info:
                service_with_assignments.delete_driver(sample_driver.id)

            assert exc_info.value.code == "DRIVER_HAS_ACTIVE_ASSIGNMENTS"

    def test_delete_already_deleted_raises_not_found(
        self, driver_service, mock_driver_repository
    ):
        """Raises NotFoundException when driver is already deleted."""
        # Arrange
        deleted_driver = Driver(
            name="Already Deleted",
            license_number="ALDEL001",
            contact_number="555-0000",
        )
        deleted_driver.soft_delete()
        mock_driver_repository.find_by_id.return_value = deleted_driver

        # Act & Assert
        with pytest.raises(NotFoundException):
            driver_service.delete_driver(deleted_driver.id)


class TestGetDriverEtag:
    """Tests for get_driver_etag method."""

    def test_get_driver_etag(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Returns ETag from repository."""
        # Arrange
        expected_etag = "abc123etag"
        mock_driver_repository.generate_etag.return_value = expected_etag

        # Act
        result = driver_service.get_driver_etag(sample_driver)

        # Assert
        assert result == expected_etag
        mock_driver_repository.generate_etag.assert_called_once_with(sample_driver)


class TestGetDriverCountsByStatus:
    """Tests for get_driver_counts_by_status method."""

    def test_get_driver_counts_by_status(self, driver_service, mock_driver_repository):
        """Returns status counts from repository."""
        # Arrange
        expected_counts = {"active": 5, "suspended": 2}
        mock_driver_repository.count_by_status.return_value = expected_counts

        # Act
        result = driver_service.get_driver_counts_by_status()

        # Assert
        assert result == expected_counts
        mock_driver_repository.count_by_status.assert_called_once()


class TestGetActiveDrivers:
    """Tests for get_active_drivers method."""

    def test_get_active_drivers(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Returns only active drivers."""
        # Arrange
        mock_driver_repository.find_active_drivers.return_value = ([sample_driver], 1)

        # Act
        result, total = driver_service.get_active_drivers(limit=50, skip=0)

        # Assert
        assert len(result) == 1
        assert total == 1
        mock_driver_repository.find_active_drivers.assert_called_once_with(
            limit=50, skip=0
        )


class TestStatusTransitionValidation:
    """Tests for status transition validation."""

    def test_suspend_driver_without_assignments_succeeds(
        self, driver_service, mock_driver_repository, sample_driver
    ):
        """Can suspend driver with no active assignments."""
        # Arrange
        mock_driver_repository.find_by_id.return_value = sample_driver
        mock_driver_repository.exists_by_license_number.return_value = False
        mock_driver_repository.update.side_effect = lambda d: d

        # Act
        result = driver_service.update_driver(
            driver_id=sample_driver.id,
            name=sample_driver.name,
            license_number=sample_driver.license_number,
            contact_number=sample_driver.contact_number,
            status=DriverStatus.SUSPENDED,
        )

        # Assert
        assert result.status == DriverStatus.SUSPENDED

    def test_activate_suspended_driver(self, driver_service, mock_driver_repository):
        """Can activate a suspended driver."""
        # Arrange
        suspended_driver = Driver(
            name="Suspended Driver",
            license_number="SUS003",
            contact_number="555-0000",
            status=DriverStatus.SUSPENDED,
        )
        mock_driver_repository.find_by_id.return_value = suspended_driver
        mock_driver_repository.exists_by_license_number.return_value = False
        mock_driver_repository.update.side_effect = lambda d: d

        # Act
        result = driver_service.update_driver(
            driver_id=suspended_driver.id,
            name=suspended_driver.name,
            license_number=suspended_driver.license_number,
            contact_number=suspended_driver.contact_number,
            status=DriverStatus.ACTIVE,
        )

        # Assert
        assert result.status == DriverStatus.ACTIVE
