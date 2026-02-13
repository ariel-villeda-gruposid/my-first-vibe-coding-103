"""
Vehicle repository for MongoDB data access.

Implements the repository pattern for Vehicle entity persistence.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.domain.models.vehicle import FuelType, Vehicle, VehicleStatus, VehicleType
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database


class VehicleRepository:
    """
    Repository for Vehicle entity CRUD operations.

    Provides data access methods for vehicles in MongoDB.
    """

    COLLECTION_NAME = "vehicles"

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
        """Create necessary indexes for the vehicles collection."""
        # Unique index on plate_number (case-insensitive)
        self._collection.create_index(
            [("plate_number", ASCENDING)],
            unique=True,
            name="idx_plate_number_unique",
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

    def _to_document(self, vehicle: Vehicle) -> Dict[str, Any]:
        """
        Convert a Vehicle domain object to a MongoDB document.

        Args:
            vehicle: Vehicle domain object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "_id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "model": vehicle.model,
            "year": vehicle.year,
            "type": vehicle.type.value,
            "fuel_type": vehicle.fuel_type.value,
            "status": vehicle.status.value,
            "created_at": vehicle.created_at,
            "updated_at": vehicle.updated_at,
            "deleted_at": vehicle.deleted_at,
        }

    def _from_document(self, doc: Dict[str, Any]) -> Vehicle:
        """
        Convert a MongoDB document to a Vehicle domain object.

        Args:
            doc: MongoDB document dictionary.

        Returns:
            Vehicle domain object.
        """
        return Vehicle(
            id=doc["_id"],
            plate_number=doc["plate_number"],
            model=doc["model"],
            year=doc["year"],
            vehicle_type=VehicleType(doc["type"]),
            fuel_type=FuelType(doc["fuel_type"]),
            status=VehicleStatus(doc["status"]),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            deleted_at=doc.get("deleted_at"),
        )

    @staticmethod
    def generate_etag(vehicle: Vehicle) -> str:
        """
        Generate an ETag for a vehicle based on its updated_at timestamp.

        Args:
            vehicle: Vehicle domain object.

        Returns:
            ETag string.
        """
        content = f"{vehicle.id}:{vehicle.updated_at.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def find_all(
        self,
        status: Optional[VehicleStatus] = None,
        vehicle_type: Optional[VehicleType] = None,
        fuel_type: Optional[FuelType] = None,
        include_deleted: bool = False,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Vehicle], int]:
        """
        Find all vehicles matching the given criteria.

        Args:
            status: Filter by vehicle status.
            vehicle_type: Filter by vehicle type.
            fuel_type: Filter by fuel type.
            include_deleted: Whether to include soft-deleted vehicles.
            limit: Maximum number of results.
            skip: Number of results to skip.
            sort_by: Field to sort by.
            sort_order: Sort direction ('asc' or 'desc').

        Returns:
            Tuple of (list of vehicles, total count).
        """
        query: Dict[str, Any] = {}

        # Exclude soft-deleted by default
        if not include_deleted:
            query["deleted_at"] = None

        # Apply filters
        if status is not None:
            query["status"] = status.value
        if vehicle_type is not None:
            query["type"] = vehicle_type.value
        if fuel_type is not None:
            query["fuel_type"] = fuel_type.value

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

        vehicles = [self._from_document(doc) for doc in cursor]
        return vehicles, total

    def find_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        """
        Find a vehicle by its ID.

        Args:
            vehicle_id: Vehicle UUID string.

        Returns:
            Vehicle if found, None otherwise.
        """
        doc = self._collection.find_one({"_id": vehicle_id})
        if doc is None:
            return None
        return self._from_document(doc)

    def find_by_plate_number(
        self, plate_number: str, include_deleted: bool = True
    ) -> Optional[Vehicle]:
        """
        Find a vehicle by its plate number (case-insensitive).

        Args:
            plate_number: Vehicle plate number.
            include_deleted: Whether to include soft-deleted vehicles.

        Returns:
            Vehicle if found, None otherwise.
        """
        normalized = plate_number.strip().upper()
        query: Dict[str, Any] = {"plate_number": normalized}

        if not include_deleted:
            query["deleted_at"] = None

        doc = self._collection.find_one(query)
        if doc is None:
            return None
        return self._from_document(doc)

    def create(self, vehicle: Vehicle) -> Vehicle:
        """
        Create a new vehicle in the database.

        Args:
            vehicle: Vehicle domain object to create.

        Returns:
            Created vehicle with generated timestamps.
        """
        doc = self._to_document(vehicle)
        self._collection.insert_one(doc)
        return vehicle

    def update(self, vehicle: Vehicle) -> Vehicle:
        """
        Update an existing vehicle in the database.

        Args:
            vehicle: Vehicle domain object with updated data.

        Returns:
            Updated vehicle.
        """
        doc = self._to_document(vehicle)
        self._collection.replace_one({"_id": vehicle.id}, doc)
        return vehicle

    def soft_delete(self, vehicle_id: str) -> bool:
        """
        Soft delete a vehicle by setting deleted_at.

        Args:
            vehicle_id: Vehicle UUID string.

        Returns:
            True if the vehicle was deleted, False if not found.
        """
        now = datetime.now(timezone.utc)
        result = self._collection.update_one(
            {"_id": vehicle_id, "deleted_at": None},
            {"$set": {"deleted_at": now, "updated_at": now}},
        )
        return result.modified_count > 0

    def restore(self, vehicle_id: str) -> bool:
        """
        Restore a soft-deleted vehicle.

        Args:
            vehicle_id: Vehicle UUID string.

        Returns:
            True if the vehicle was restored, False if not found.
        """
        now = datetime.now(timezone.utc)
        result = self._collection.update_one(
            {"_id": vehicle_id, "deleted_at": {"$ne": None}},
            {"$set": {"deleted_at": None, "updated_at": now}},
        )
        return result.modified_count > 0

    def exists_by_plate_number(
        self, plate_number: str, exclude_id: Optional[str] = None
    ) -> bool:
        """
        Check if a vehicle with the given plate number exists.

        Args:
            plate_number: Plate number to check.
            exclude_id: Vehicle ID to exclude from the check.

        Returns:
            True if a vehicle with the plate number exists.
        """
        normalized = plate_number.strip().upper()
        query: Dict[str, Any] = {"plate_number": normalized}

        if exclude_id is not None:
            query["_id"] = {"$ne": exclude_id}

        return self._collection.count_documents(query, limit=1) > 0

    def count_by_status(self) -> Dict[str, int]:
        """
        Count vehicles grouped by status (excluding soft-deleted).

        Returns:
            Dictionary mapping status to count.
        """
        pipeline = [
            {"$match": {"deleted_at": None}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        result = list(self._collection.aggregate(pipeline))
        return {doc["_id"]: doc["count"] for doc in result}
