"""
Unit tests for Driver domain model.

Tests the Driver class, enums, and domain logic.
"""

import uuid
from datetime import datetime, timezone

import pytest
from app.domain.models.driver import Driver, DriverStatus


class TestDriverStatus:
    """Tests for DriverStatus enum."""

    def test_status_values(self):
        """Verify all expected status values exist."""
        # Arrange & Act & Assert
        assert DriverStatus.ACTIVE.value == "active"
        assert DriverStatus.SUSPENDED.value == "suspended"

    def test_status_from_string(self):
        """Can create status from string value."""
        # Arrange & Act & Assert
        assert DriverStatus("active") == DriverStatus.ACTIVE
        assert DriverStatus("suspended") == DriverStatus.SUSPENDED


class TestDriverCreation:
    """Tests for Driver creation."""

    def test_create_driver_with_all_fields(self):
        """Driver can be created with all fields."""
        # Arrange
        name = "John Doe"
        license_number = "DL12345"
        contact_number = "+1-555-123-4567"
        status = DriverStatus.ACTIVE

        # Act
        driver = Driver(
            name=name,
            license_number=license_number,
            contact_number=contact_number,
            status=status,
        )

        # Assert
        assert driver.name == name
        assert driver.license_number == "DL12345"  # Normalized to uppercase
        assert driver.contact_number == contact_number
        assert driver.status == status
        assert driver.is_deleted() is False
        assert driver.deleted_at is None

    def test_create_driver_generates_uuid_id(self):
        """New driver gets a valid UUID string as ID."""
        # Arrange & Act
        driver = Driver(
            name="Jane Smith",
            license_number="LIC999",
            contact_number="555-1234",
        )

        # Assert
        assert driver.id is not None
        # Verify it's a valid UUID
        uuid.UUID(driver.id)

    def test_create_driver_sets_timestamps(self):
        """New driver gets created_at and updated_at timestamps."""
        # Arrange
        before_creation = datetime.now(timezone.utc)

        # Act
        driver = Driver(
            name="Test Driver",
            license_number="TEST001",
            contact_number="555-0000",
        )

        after_creation = datetime.now(timezone.utc)

        # Assert
        assert driver.created_at is not None
        assert driver.updated_at is not None
        assert before_creation <= driver.created_at <= after_creation
        assert driver.created_at == driver.updated_at

    def test_create_driver_default_status_is_active(self):
        """New driver has ACTIVE status by default."""
        # Arrange & Act
        driver = Driver(
            name="Default Status Driver",
            license_number="DEF001",
            contact_number="555-1111",
        )

        # Assert
        assert driver.status == DriverStatus.ACTIVE

    def test_create_driver_with_explicit_id(self):
        """Driver can be created with a specific ID."""
        # Arrange
        specific_id = str(uuid.uuid4())

        # Act
        driver = Driver(
            id=specific_id,
            name="Specific ID Driver",
            license_number="SPC001",
            contact_number="555-2222",
        )

        # Assert
        assert driver.id == specific_id


class TestDriverLicenseNormalization:
    """Tests for license number normalization."""

    def test_license_number_normalized_to_uppercase(self):
        """License number is converted to uppercase."""
        # Arrange & Act
        driver = Driver(
            name="Test",
            license_number="abc123",
            contact_number="555-0000",
        )

        # Assert
        assert driver.license_number == "ABC123"

    def test_license_number_trimmed(self):
        """License number has whitespace trimmed."""
        # Arrange & Act
        driver = Driver(
            name="Test",
            license_number="  XYZ789  ",
            contact_number="555-0000",
        )

        # Assert
        assert driver.license_number == "XYZ789"

    def test_license_number_mixed_case_and_spaces(self):
        """License number handles mixed case and spaces."""
        # Arrange & Act
        driver = Driver(
            name="Test",
            license_number="  AbC123dEf  ",
            contact_number="555-0000",
        )

        # Assert
        assert driver.license_number == "ABC123DEF"


class TestDriverNameNormalization:
    """Tests for name normalization."""

    def test_name_trimmed(self):
        """Name has whitespace trimmed."""
        # Arrange & Act
        driver = Driver(
            name="  John Doe  ",
            license_number="TEST001",
            contact_number="555-0000",
        )

        # Assert
        assert driver.name == "John Doe"


class TestDriverContactNormalization:
    """Tests for contact number normalization."""

    def test_contact_number_trimmed(self):
        """Contact number has whitespace trimmed."""
        # Arrange & Act
        driver = Driver(
            name="Test",
            license_number="TEST001",
            contact_number="  555-1234  ",
        )

        # Assert
        assert driver.contact_number == "555-1234"


class TestDriverValidation:
    """Tests for driver validation methods."""

    def test_validate_license_number_valid_alphanumeric(self):
        """Valid alphanumeric license number passes validation."""
        # Arrange & Act & Assert
        assert Driver.validate_license_number("ABC123") is True
        assert Driver.validate_license_number("XYZ789DEF") is True
        assert Driver.validate_license_number("A1B2C3") is True

    def test_validate_license_number_invalid_characters(self):
        """License numbers with special characters fail validation."""
        # Arrange & Act & Assert
        assert Driver.validate_license_number("ABC-123") is False
        assert Driver.validate_license_number("ABC 123") is False
        assert Driver.validate_license_number("ABC_123") is False
        assert Driver.validate_license_number("ABC.123") is False

    def test_validate_license_number_empty(self):
        """Empty license number fails validation."""
        # Arrange & Act & Assert
        assert Driver.validate_license_number("") is False
        assert Driver.validate_license_number("   ") is False

    def test_validate_contact_number_valid_formats(self):
        """Valid phone formats pass validation."""
        # Arrange & Act & Assert
        assert Driver.validate_contact_number("+1-555-123-4567") is True
        assert Driver.validate_contact_number("555-123-4567") is True
        assert Driver.validate_contact_number("(555) 123-4567") is True
        assert Driver.validate_contact_number("+44 20 7123 4567") is True
        assert Driver.validate_contact_number("5551234567") is True

    def test_validate_contact_number_too_short(self):
        """Phone numbers that are too short fail validation."""
        # Arrange & Act & Assert
        assert Driver.validate_contact_number("123456") is False  # 6 chars, need 7+
        assert Driver.validate_contact_number("1234") is False

    def test_validate_contact_number_too_long(self):
        """Phone numbers that are too long fail validation."""
        # Arrange & Act & Assert
        assert (
            Driver.validate_contact_number("123456789012345678901") is False
        )  # 21 chars

    def test_validate_contact_number_invalid_characters(self):
        """Phone numbers with invalid characters fail validation."""
        # Arrange & Act & Assert
        assert Driver.validate_contact_number("abc-def-ghij") is False
        assert Driver.validate_contact_number("555#123#4567") is False


class TestDriverStatusMethods:
    """Tests for driver status-related methods."""

    def test_is_active_for_active_driver(self):
        """Active non-deleted driver returns True."""
        # Arrange
        driver = Driver(
            name="Active Driver",
            license_number="ACT001",
            contact_number="555-1234",
            status=DriverStatus.ACTIVE,
        )

        # Act & Assert
        assert driver.is_active() is True

    def test_is_active_for_suspended_driver(self):
        """Suspended driver returns False for is_active."""
        # Arrange
        driver = Driver(
            name="Suspended Driver",
            license_number="SUS001",
            contact_number="555-1234",
            status=DriverStatus.SUSPENDED,
        )

        # Act & Assert
        assert driver.is_active() is False

    def test_is_active_for_deleted_driver(self):
        """Deleted driver returns False for is_active."""
        # Arrange
        driver = Driver(
            name="Deleted Driver",
            license_number="DEL001",
            contact_number="555-1234",
            status=DriverStatus.ACTIVE,
        )
        driver.soft_delete()

        # Act & Assert
        assert driver.is_active() is False

    def test_can_receive_assignments_active_driver(self):
        """Active driver can receive assignments."""
        # Arrange
        driver = Driver(
            name="Active Driver",
            license_number="ACT002",
            contact_number="555-1234",
            status=DriverStatus.ACTIVE,
        )

        # Act & Assert
        assert driver.can_receive_assignments() is True

    def test_can_receive_assignments_suspended_driver(self):
        """Suspended driver cannot receive assignments."""
        # Arrange
        driver = Driver(
            name="Suspended Driver",
            license_number="SUS002",
            contact_number="555-1234",
            status=DriverStatus.SUSPENDED,
        )

        # Act & Assert
        assert driver.can_receive_assignments() is False

    def test_is_deleted_for_new_driver(self):
        """New driver is not deleted."""
        # Arrange
        driver = Driver(
            name="New Driver",
            license_number="NEW001",
            contact_number="555-1234",
        )

        # Act & Assert
        assert driver.is_deleted() is False

    def test_is_deleted_after_soft_delete(self):
        """Driver is deleted after soft_delete."""
        # Arrange
        driver = Driver(
            name="To Be Deleted",
            license_number="TBD001",
            contact_number="555-1234",
        )

        # Act
        driver.soft_delete()

        # Assert
        assert driver.is_deleted() is True


class TestDriverSoftDelete:
    """Tests for soft delete functionality."""

    def test_soft_delete_sets_deleted_at(self):
        """Soft delete sets the deleted_at timestamp."""
        # Arrange
        driver = Driver(
            name="To Delete",
            license_number="DEL002",
            contact_number="555-1234",
        )
        before_delete = datetime.now(timezone.utc)

        # Act
        driver.soft_delete()

        after_delete = datetime.now(timezone.utc)

        # Assert
        assert driver.deleted_at is not None
        assert before_delete <= driver.deleted_at <= after_delete

    def test_soft_delete_updates_updated_at(self):
        """Soft delete also updates updated_at."""
        # Arrange
        driver = Driver(
            name="To Delete",
            license_number="DEL003",
            contact_number="555-1234",
        )
        original_updated_at = driver.updated_at

        # Wait a tiny bit to ensure timestamp changes
        import time

        time.sleep(0.001)

        # Act
        driver.soft_delete()

        # Assert
        assert driver.updated_at > original_updated_at


class TestDriverUpdate:
    """Tests for driver update functionality."""

    def test_update_all_fields(self):
        """Update can change all fields."""
        # Arrange
        driver = Driver(
            name="Original Name",
            license_number="ORI001",
            contact_number="555-0000",
            status=DriverStatus.ACTIVE,
        )
        original_updated_at = driver.updated_at

        import time

        time.sleep(0.001)

        # Act
        driver.update(
            name="New Name",
            license_number="NEW001",
            contact_number="555-9999",
            status=DriverStatus.SUSPENDED,
        )

        # Assert
        assert driver.name == "New Name"
        assert driver.license_number == "NEW001"
        assert driver.contact_number == "555-9999"
        assert driver.status == DriverStatus.SUSPENDED
        assert driver.updated_at > original_updated_at

    def test_update_partial_fields(self):
        """Update changes only provided fields."""
        # Arrange
        driver = Driver(
            name="Original Name",
            license_number="ORI002",
            contact_number="555-0000",
            status=DriverStatus.ACTIVE,
        )

        # Act
        driver.update(name="New Name Only")

        # Assert
        assert driver.name == "New Name Only"
        assert driver.license_number == "ORI002"  # Unchanged
        assert driver.contact_number == "555-0000"  # Unchanged
        assert driver.status == DriverStatus.ACTIVE  # Unchanged

    def test_update_license_number_normalization(self):
        """Update normalizes license number."""
        # Arrange
        driver = Driver(
            name="Test",
            license_number="ORI003",
            contact_number="555-0000",
        )

        # Act
        driver.update(license_number="  abc123  ")

        # Assert
        assert driver.license_number == "ABC123"


class TestDriverSerialization:
    """Tests for driver serialization."""

    def test_to_dict(self):
        """Driver can be converted to dictionary."""
        # Arrange
        driver = Driver(
            id="test-uuid-123",
            name="Test Driver",
            license_number="TEST001",
            contact_number="555-1234",
            status=DriverStatus.ACTIVE,
        )

        # Act
        result = driver.to_dict()

        # Assert
        assert result["id"] == "test-uuid-123"
        assert result["name"] == "Test Driver"
        assert result["license_number"] == "TEST001"
        assert result["contact_number"] == "555-1234"
        assert result["status"] == "active"
        assert "created_at" in result
        assert "updated_at" in result
        assert result["deleted_at"] is None

    def test_from_dict(self):
        """Driver can be created from dictionary."""
        # Arrange
        data = {
            "id": "dict-uuid-456",
            "name": "From Dict Driver",
            "license_number": "FRM001",
            "contact_number": "555-5678",
            "status": "suspended",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "deleted_at": None,
        }

        # Act
        driver = Driver.from_dict(data)

        # Assert
        assert driver.id == "dict-uuid-456"
        assert driver.name == "From Dict Driver"
        assert driver.license_number == "FRM001"
        assert driver.contact_number == "555-5678"
        assert driver.status == DriverStatus.SUSPENDED


class TestDriverEquality:
    """Tests for driver equality and hashing."""

    def test_same_id_are_equal(self):
        """Drivers with same ID are equal."""
        # Arrange
        driver1 = Driver(
            id="same-id",
            name="Driver One",
            license_number="D1",
            contact_number="555-1111",
        )
        driver2 = Driver(
            id="same-id",
            name="Driver Two",
            license_number="D2",
            contact_number="555-2222",
        )

        # Act & Assert
        assert driver1 == driver2

    def test_different_id_not_equal(self):
        """Drivers with different IDs are not equal."""
        # Arrange
        driver1 = Driver(
            id="id-one",
            name="Same Name",
            license_number="SAM001",
            contact_number="555-1234",
        )
        driver2 = Driver(
            id="id-two",
            name="Same Name",
            license_number="SAM001",
            contact_number="555-1234",
        )

        # Act & Assert
        assert driver1 != driver2

    def test_hash_based_on_id(self):
        """Driver hash is based on ID."""
        # Arrange
        driver1 = Driver(
            id="hash-id",
            name="Test",
            license_number="HSH001",
            contact_number="555-0000",
        )
        driver2 = Driver(
            id="hash-id",
            name="Different",
            license_number="HSH002",
            contact_number="555-9999",
        )

        # Act & Assert
        assert hash(driver1) == hash(driver2)

    def test_not_equal_to_non_driver(self):
        """Driver is not equal to non-Driver objects."""
        # Arrange
        driver = Driver(
            name="Test",
            license_number="NON001",
            contact_number="555-0000",
        )

        # Act & Assert
        assert driver != "not a driver"
        assert driver != 123
        assert driver != {"name": "Test"}


class TestDriverRepr:
    """Tests for driver string representation."""

    def test_repr_format(self):
        """Driver repr has expected format."""
        # Arrange
        driver = Driver(
            id="repr-id",
            name="Repr Driver",
            license_number="RPR001",
            contact_number="555-1234",
            status=DriverStatus.ACTIVE,
        )

        # Act
        result = repr(driver)

        # Assert
        assert "Driver(" in result
        assert "repr-id" in result
        assert "Repr Driver" in result
        assert "RPR001" in result
        assert "active" in result
