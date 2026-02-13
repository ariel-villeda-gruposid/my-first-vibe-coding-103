"""
Driver repository for MongoDB data access.

Implements the repository pattern for Driver entity persistence.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.domain.models.driver import Driver, DriverStatus
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database


class DriverRepository:
    """
    Repository for Driver entity CRUD operations.

    Provides data access methods for drivers in MongoDB.
    """

    COLLECTION_NAME = "drivers"

    def __init__(self, db: Database) -> None:
        """
        Initialize the repository with a database connection.

        Args:
            db: MongoDB database instance.
        """
        self._db = db
        self._collection: Collection = db[self.COLLECTION_NAME]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create necessary indexes for the drivers collection."""
        # Unique index on license_number (case-insensitive)
        self._collection.create_index(
            [("license_number", ASCENDING)],
            unique=True,
            name="idx_license_number_unique",
        )
        # Index for status filtering
        self._collection.create_index(
            [("status", ASCENDING)],
            name="idx_status",
        )
        # Index for sorting by updated_at
        self._collection.create_index(
            [("updated_at", DESCENDING)],
            name="idx_updated_at",
        )
        # Compound index for soft delete filtering
        self._collection.create_index(
            [("deleted_at", ASCENDING), ("status", ASCENDING)],
            name="idx_deleted_status",
        )

    def _to_document(self, driver: Driver) -> Dict[str, Any]:
        """
        Convert a Driver domain object to a MongoDB document.

        Args:
            driver: Driver domain object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "_id": driver.id,
            "name": driver.name,
            "license_number": driver.license_number,
            "contact_number": driver.contact_number,
            "status": driver.status.value,
            "created_at": driver.created_at,
            "updated_at": driver.updated_at,
            "deleted_at": driver.deleted_at,
        }

    def _from_document(self, doc: Dict[str, Any]) -> Driver:
        """
        Convert a MongoDB document to a Driver domain object.

        Args:
            doc: MongoDB document dictionary.

        Returns:
            Driver domain object.
        """
        return Driver(
            id=doc["_id"],
            name=doc["name"],
            license_number=doc["license_number"],
            contact_number=doc["contact_number"],
            status=DriverStatus(doc["status"]),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            deleted_at=doc.get("deleted_at"),
        )

    @staticmethod
    def generate_etag(driver: Driver) -> str:
        """
        Generate an ETag for a driver based on its updated_at timestamp.

        Args:
            driver: Driver domain object.

        Returns:
            ETag string.
        """
        content = f"{driver.id}:{driver.updated_at.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def find_all(
        self,
        status: Optional[DriverStatus] = None,
        include_deleted: bool = False,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Driver], int]:
        """
        Find all drivers matching the given criteria.

        Args:
            status: Filter by driver status.
            include_deleted: Whether to include soft-deleted drivers.
            limit: Maximum number of results.
            skip: Number of results to skip.
            sort_by: Field to sort by.
            sort_order: Sort direction ('asc' or 'desc').

        Returns:
            Tuple of (list of drivers, total count).
        """
        query: Dict[str, Any] = {}

        # Exclude soft-deleted by default
        if not include_deleted:
            query["deleted_at"] = None

        # Apply filters
        if status is not None:
            query["status"] = status.value

        # Get total count
        total = self._collection.count_documents(query)

        # Determine sort direction
        sort_direction = DESCENDING if sort_order == "desc" else ASCENDING

        # Execute query with pagination
        cursor = (
            self._collection.find(query)
            .sort(sort_by, sort_direction)
            .skip(skip)
            .limit(limit)
        )

        drivers = [self._from_document(doc) for doc in cursor]
        return drivers, total

    def find_by_id(self, driver_id: str) -> Optional[Driver]:
        """
        Find a driver by its ID.

        Args:
            driver_id: Driver UUID string.

        Returns:
            Driver if found, None otherwise.
        """
        doc = self._collection.find_one({"_id": driver_id})
        if doc is None:
            return None
        return self._from_document(doc)

    def find_by_license_number(
        self, license_number: str, include_deleted: bool = True
    ) -> Optional[Driver]:
        """
        Find a driver by their license number (case-insensitive).

        Args:
            license_number: Driver license number.
            include_deleted: Whether to include soft-deleted drivers.

        Returns:
            Driver if found, None otherwise.
        """
        normalized = license_number.strip().upper()
        query: Dict[str, Any] = {"license_number": normalized}

        if not include_deleted:
            query["deleted_at"] = None

        doc = self._collection.find_one(query)
        if doc is None:
            return None
        return self._from_document(doc)

    def create(self, driver: Driver) -> Driver:
        """
        Create a new driver in the database.

        Args:
            driver: Driver domain object to create.

        Returns:
            Created driver with generated timestamps.
        """
        doc = self._to_document(driver)
        self._collection.insert_one(doc)
        return driver

    def update(self, driver: Driver) -> Driver:
        """
        Update an existing driver in the database.

        Args:
            driver: Driver domain object with updated data.

        Returns:
            Updated driver.
        """
        doc = self._to_document(driver)
        self._collection.replace_one({"_id": driver.id}, doc)
        return driver

    def soft_delete(self, driver_id: str) -> bool:
        """
        Soft delete a driver by setting deleted_at.

        Args:
            driver_id: Driver UUID string.

        Returns:
            True if the driver was deleted, False if not found.
        """
        now = datetime.now(timezone.utc)
        result = self._collection.update_one(
            {"_id": driver_id, "deleted_at": None},
            {"$set": {"deleted_at": now, "updated_at": now}},
        )
        return result.modified_count > 0

    def restore(self, driver_id: str) -> bool:
        """
        Restore a soft-deleted driver.

        Args:
            driver_id: Driver UUID string.

        Returns:
            True if the driver was restored, False if not found.
        """
        now = datetime.now(timezone.utc)
        result = self._collection.update_one(
            {"_id": driver_id, "deleted_at": {"$ne": None}},
            {"$set": {"deleted_at": None, "updated_at": now}},
        )
        return result.modified_count > 0

    def exists_by_license_number(
        self, license_number: str, exclude_id: Optional[str] = None
    ) -> bool:
        """
        Check if a driver with the given license number exists.

        Args:
            license_number: License number to check.
            exclude_id: Driver ID to exclude from the check.

        Returns:
            True if a driver with the license number exists.
        """
        normalized = license_number.strip().upper()
        query: Dict[str, Any] = {"license_number": normalized}

        if exclude_id is not None:
            query["_id"] = {"$ne": exclude_id}

        return self._collection.count_documents(query, limit=1) > 0

    def count_by_status(self) -> Dict[str, int]:
        """
        Count drivers grouped by status (excluding soft-deleted).

        Returns:
            Dictionary mapping status to count.
        """
        pipeline = [
            {"$match": {"deleted_at": None}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        result = list(self._collection.aggregate(pipeline))
        return {doc["_id"]: doc["count"] for doc in result}

    def find_active_drivers(
        self, limit: int = 100, skip: int = 0
    ) -> Tuple[List[Driver], int]:
        """
        Find all active (non-deleted, ACTIVE status) drivers.

        Args:
            limit: Maximum number of results.
            skip: Number of results to skip.

        Returns:
            Tuple of (list of active drivers, total count).
        """
        return self.find_all(
            status=DriverStatus.ACTIVE,
            include_deleted=False,
            limit=limit,
            skip=skip,
        )
