"""
Unit tests for Assignment domain model.

Tests the Assignment entity behavior, validation, and state transitions.
"""

from datetime import datetime, timedelta, timezone

import pytest
from app.domain.models.assignment import Assignment


class TestAssignmentCreation:
    """Test Assignment instantiation and validation."""

    def test_create_assignment_with_all_fields(self):
        """Should create assignment with all fields."""
        now = datetime.now(timezone.utc)
        start = now
        end = now + timedelta(hours=8)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=start,
            end_datetime=end,
            notes="Test assignment",
            created_at=now,
            updated_at=now,
        )

        assert assignment.id == "uuid-123"
        assert assignment.driver_id == "driver-456"
        assert assignment.vehicle_id == "vehicle-789"
        assert assignment.start_datetime == start
        assert assignment.end_datetime == end
        assert assignment.notes == "Test assignment"
        assert assignment.created_at == now
        assert assignment.updated_at == now

    def test_create_assignment_without_end_datetime(self):
        """Should create ongoing assignment without end_datetime."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment.end_datetime is None
        assert assignment.notes is None

    def test_create_assignment_without_notes(self):
        """Should create assignment without notes."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment.notes is None


class TestAssignmentIsActive:
    """Test is_active() method."""

    def test_is_active_when_no_end_datetime(self):
        """Assignment with no end_datetime is active."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=1),
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment.is_active() is True

    def test_is_active_when_end_datetime_in_future(self):
        """Assignment with future end_datetime is active."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=1),
            end_datetime=now + timedelta(hours=8),
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment.is_active() is True

    def test_is_not_active_when_end_datetime_in_past(self):
        """Assignment with past end_datetime is not active."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=8),
            end_datetime=now - timedelta(hours=1),
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment.is_active() is False

    def test_is_not_active_when_end_datetime_equals_now(self):
        """Assignment ending exactly now is not active."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=8),
            end_datetime=now,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        # End datetime == now means it just ended, so not active
        assert assignment.is_active() is False


class TestAssignmentClose:
    """Test close() method."""

    def test_close_sets_end_datetime_to_now(self):
        """close() should set end_datetime to current time."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=1),
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment.end_datetime is None

        assignment.close()

        assert assignment.end_datetime is not None
        assert assignment.end_datetime <= datetime.now(timezone.utc)
        assert assignment.end_datetime > now - timedelta(seconds=1)

    def test_close_updates_updated_at(self):
        """close() should update the updated_at timestamp."""
        old_time = datetime.now(timezone.utc) - timedelta(hours=1)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=old_time,
            end_datetime=None,
            notes=None,
            created_at=old_time,
            updated_at=old_time,
        )

        assignment.close()

        assert assignment.updated_at > old_time


class TestAssignmentUpdate:
    """Test update() method."""

    def test_update_notes(self):
        """update() should change notes."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assignment.update(notes="Updated notes")

        assert assignment.notes == "Updated notes"

    def test_update_notes_trims_trailing_whitespace(self):
        """update() should trim trailing whitespace from notes."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assignment.update(notes="Updated notes   ")

        assert assignment.notes == "Updated notes"

    def test_update_notes_with_empty_string_sets_none(self):
        """update() with empty notes should set to None."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes="Some notes",
            created_at=now,
            updated_at=now,
        )

        assignment.update(notes="")

        assert assignment.notes is None

    def test_update_notes_with_whitespace_only_sets_none(self):
        """update() with whitespace-only notes should set to None."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes="Some notes",
            created_at=now,
            updated_at=now,
        )

        assignment.update(notes="   ")

        assert assignment.notes is None

    def test_update_notes_exceeding_max_length_raises_error(self):
        """update() with notes > MAX_NOTES_LENGTH should raise ValueError."""
        now = datetime.now(timezone.utc)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        long_notes = "x" * 200

        with pytest.raises(ValueError) as exc_info:
            assignment.update(notes=long_notes)

        assert "127" in str(exc_info.value)

    def test_update_updates_updated_at(self):
        """update() should update the updated_at timestamp."""
        old_time = datetime.now(timezone.utc) - timedelta(hours=1)

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=old_time,
            end_datetime=None,
            notes=None,
            created_at=old_time,
            updated_at=old_time,
        )

        assignment.update(notes="New notes")

        assert assignment.updated_at > old_time


class TestAssignmentValidation:
    """Test Assignment field validation."""

    def test_notes_max_length_constant(self):
        """MAX_NOTES_LENGTH should be 127."""
        assert Assignment.MAX_NOTES_LENGTH == 127

    def test_notes_at_max_length_accepted(self):
        """Notes at exactly MAX_NOTES_LENGTH should be accepted."""
        now = datetime.now(timezone.utc)
        notes = "x" * 127

        assignment = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

        assert len(assignment.notes) == 127


class TestAssignmentEquality:
    """Test Assignment comparison and hashing."""

    def test_assignments_with_same_id_are_equal(self):
        """Assignments with same ID should be equal."""
        now = datetime.now(timezone.utc)

        assignment1 = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assignment2 = Assignment(
            id="uuid-123",
            driver_id="driver-999",  # Different driver
            vehicle_id="vehicle-999",  # Different vehicle
            start_datetime=now + timedelta(hours=1),  # Different time
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment1 == assignment2

    def test_assignments_with_different_ids_are_not_equal(self):
        """Assignments with different IDs should not be equal."""
        now = datetime.now(timezone.utc)

        assignment1 = Assignment(
            id="uuid-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assignment2 = Assignment(
            id="uuid-456",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now,
            end_datetime=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )

        assert assignment1 != assignment2
