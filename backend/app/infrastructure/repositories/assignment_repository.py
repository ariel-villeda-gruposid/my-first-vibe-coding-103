"""
Assignment repository for MongoDB data access.

Implements the repository pattern for Assignment entity persistence.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.domain.models.assignment import Assignment
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database


class AssignmentRepository:
    """
    Repository for Assignment entity CRUD operations.

    Provides data access methods for assignments in MongoDB.
    """

    COLLECTION_NAME = "assignments"

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
        """Create necessary indexes for the assignments collection."""
        # Index for driver queries
        self._collection.create_index(
            [("driver_id", ASCENDING)],
            name="idx_driver_id",
        )
        # Index for vehicle queries
        self._collection.create_index(
            [("vehicle_id", ASCENDING)],
            name="idx_vehicle_id",
        )
        # Index for active assignment queries (end_datetime null or future)
        self._collection.create_index(
            [("driver_id", ASCENDING), ("end_datetime", ASCENDING)],
            name="idx_driver_active",
        )
        self._collection.create_index(
            [("vehicle_id", ASCENDING), ("end_datetime", ASCENDING)],
            name="idx_vehicle_active",
        )
        # Index for sorting by start_datetime
        self._collection.create_index(
            [("start_datetime", DESCENDING)],
            name="idx_start_datetime",
        )
        # Index for overlap detection
        self._collection.create_index(
            [
                ("driver_id", ASCENDING),
                ("start_datetime", ASCENDING),
                ("end_datetime", ASCENDING),
            ],
            name="idx_driver_overlap",
        )
        self._collection.create_index(
            [
                ("vehicle_id", ASCENDING),
                ("start_datetime", ASCENDING),
                ("end_datetime", ASCENDING),
            ],
            name="idx_vehicle_overlap",
        )

    def _to_document(self, assignment: Assignment) -> Dict[str, Any]:
        """
        Convert an Assignment domain object to a MongoDB document.

        Args:
            assignment: Assignment domain object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "_id": assignment.id,
            "driver_id": assignment.driver_id,
            "vehicle_id": assignment.vehicle_id,
            "start_datetime": assignment.start_datetime,
            "end_datetime": assignment.end_datetime,
            "notes": assignment.notes,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
        }

    def _from_document(self, doc: Dict[str, Any]) -> Assignment:
        """
        Convert a MongoDB document to an Assignment domain object.

        Args:
            doc: MongoDB document dictionary.

        Returns:
            Assignment domain object.
        """
        return Assignment(
            id=doc["_id"],
            driver_id=doc["driver_id"],
            vehicle_id=doc["vehicle_id"],
            start_datetime=doc["start_datetime"],
            end_datetime=doc.get("end_datetime"),
            notes=doc.get("notes"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )

    @staticmethod
    def generate_etag(assignment: Assignment) -> str:
        """
        Generate an ETag for an assignment based on its updated_at timestamp.

        Args:
            assignment: Assignment domain object.

        Returns:
            ETag string.
        """
        content = f"{assignment.id}:{assignment.updated_at.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def find_all(
        self,
        driver_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        active_only: bool = False,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "start_datetime",
        sort_order: str = "desc",
    ) -> Tuple[List[Assignment], int]:
        """
        Find all assignments matching the given criteria.

        Args:
            driver_id: Filter by driver ID.
            vehicle_id: Filter by vehicle ID.
            active_only: If True, only return active assignments.
            limit: Maximum number of results.
            skip: Number of results to skip.
            sort_by: Field to sort by.
            sort_order: Sort direction ('asc' or 'desc').

        Returns:
            Tuple of (list of assignments, total count).
        """
        query: Dict[str, Any] = {}

        if driver_id is not None:
            query["driver_id"] = driver_id
        if vehicle_id is not None:
            query["vehicle_id"] = vehicle_id
        if active_only:
            now = datetime.now(timezone.utc)
            query["$or"] = [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ]

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

        assignments = [self._from_document(doc) for doc in cursor]
        return assignments, total

    def find_by_id(self, assignment_id: str) -> Optional[Assignment]:
        """
        Find an assignment by its ID.

        Args:
            assignment_id: Assignment UUID string.

        Returns:
            Assignment if found, None otherwise.
        """
        doc = self._collection.find_one({"_id": assignment_id})
        if doc is None:
            return None
        return self._from_document(doc)

    def create(self, assignment: Assignment) -> Assignment:
        """
        Create a new assignment in the database.

        Args:
            assignment: Assignment domain object to create.

        Returns:
            Created assignment.
        """
        doc = self._to_document(assignment)
        self._collection.insert_one(doc)
        return assignment

    def update(self, assignment: Assignment) -> Assignment:
        """
        Update an existing assignment in the database.

        Args:
            assignment: Assignment domain object with updated data.

        Returns:
            Updated assignment.
        """
        doc = self._to_document(assignment)
        self._collection.replace_one({"_id": assignment.id}, doc)
        return assignment

    def delete(self, assignment_id: str) -> bool:
        """
        Delete an assignment (hard delete).

        Args:
            assignment_id: Assignment UUID string.

        Returns:
            True if the assignment was deleted, False if not found.
        """
        result = self._collection.delete_one({"_id": assignment_id})
        return result.deleted_count > 0

    def has_active_assignment_for_driver(self, driver_id: str) -> bool:
        """
        Check if a driver has any active assignment.

        Args:
            driver_id: Driver UUID to check.

        Returns:
            True if driver has an active assignment.
        """
        now = datetime.now(timezone.utc)
        query = {
            "driver_id": driver_id,
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        return self._collection.count_documents(query, limit=1) > 0

    def has_active_assignment_for_vehicle(self, vehicle_id: str) -> bool:
        """
        Check if a vehicle has any active assignment.

        Args:
            vehicle_id: Vehicle UUID to check.

        Returns:
            True if vehicle has an active assignment.
        """
        now = datetime.now(timezone.utc)
        query = {
            "vehicle_id": vehicle_id,
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        return self._collection.count_documents(query, limit=1) > 0

    def find_active_assignment_for_driver(self, driver_id: str) -> Optional[Assignment]:
        """
        Find the active assignment for a driver.

        Args:
            driver_id: Driver UUID.

        Returns:
            Active assignment if exists, None otherwise.
        """
        now = datetime.now(timezone.utc)
        query = {
            "driver_id": driver_id,
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        doc = self._collection.find_one(query)
        if doc is None:
            return None
        return self._from_document(doc)

    def find_active_assignment_for_vehicle(
        self, vehicle_id: str
    ) -> Optional[Assignment]:
        """
        Find the active assignment for a vehicle.

        Args:
            vehicle_id: Vehicle UUID.

        Returns:
            Active assignment if exists, None otherwise.
        """
        now = datetime.now(timezone.utc)
        query = {
            "vehicle_id": vehicle_id,
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        doc = self._collection.find_one(query)
        if doc is None:
            return None
        return self._from_document(doc)

    def close_active_assignments_for_driver(self, driver_id: str) -> int:
        """
        Close all active assignments for a driver.

        Args:
            driver_id: Driver UUID.

        Returns:
            Number of assignments closed.
        """
        now = datetime.now(timezone.utc)
        query = {
            "driver_id": driver_id,
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        result = self._collection.update_many(
            query,
            {"$set": {"end_datetime": now, "updated_at": now}},
        )
        return result.modified_count

    def close_active_assignments_for_vehicle(self, vehicle_id: str) -> int:
        """
        Close all active assignments for a vehicle.

        Args:
            vehicle_id: Vehicle UUID.

        Returns:
            Number of assignments closed.
        """
        now = datetime.now(timezone.utc)
        query = {
            "vehicle_id": vehicle_id,
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        result = self._collection.update_many(
            query,
            {"$set": {"end_datetime": now, "updated_at": now}},
        )
        return result.modified_count

    def count_active(self) -> int:
        """
        Count all active assignments.

        Returns:
            Number of active assignments.
        """
        now = datetime.now(timezone.utc)
        query = {
            "$or": [
                {"end_datetime": None},
                {"end_datetime": {"$gt": now}},
            ],
        }
        return self._collection.count_documents(query)

    def count_all(self) -> int:
        """
        Count all assignments.

        Returns:
            Total number of assignments.
        """
        return self._collection.count_documents({})

    def has_overlapping_assignment(
        self,
        driver_id: Optional[str],
        vehicle_id: Optional[str],
        start_datetime: datetime,
        end_datetime: Optional[datetime],
        exclude_id: Optional[str] = None,
    ) -> bool:
        """
        Check if there would be an overlapping assignment.

        Args:
            driver_id: Driver to check (optional).
            vehicle_id: Vehicle to check (optional).
            start_datetime: Start of the period.
            end_datetime: End of the period (None for ongoing).
            exclude_id: Assignment ID to exclude from check.

        Returns:
            True if there would be overlap.
        """
        # Build queries for driver and vehicle separately
        queries = []

        if driver_id:
            driver_query = self._build_overlap_query(
                "driver_id", driver_id, start_datetime, end_datetime, exclude_id
            )
            if driver_query:
                queries.append(driver_query)

        if vehicle_id:
            vehicle_query = self._build_overlap_query(
                "vehicle_id", vehicle_id, start_datetime, end_datetime, exclude_id
            )
            if vehicle_query:
                queries.append(vehicle_query)

        if not queries:
            return False

        for query in queries:
            if self._collection.count_documents(query, limit=1) > 0:
                return True

        return False

    def _build_overlap_query(
        self,
        id_field: str,
        id_value: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime],
        exclude_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a query to detect overlapping assignments.

        Two assignments overlap if:
        - They both cover some common time period
        - For an ongoing assignment (end_datetime=None), it overlaps with any future assignment

        Args:
            id_field: Field name ('driver_id' or 'vehicle_id').
            id_value: ID value to filter by.
            start_datetime: Start of new assignment.
            end_datetime: End of new assignment (None for ongoing).
            exclude_id: Assignment ID to exclude.

        Returns:
            Query dictionary.
        """
        query: Dict[str, Any] = {id_field: id_value}

        if exclude_id:
            query["_id"] = {"$ne": exclude_id}

        # Overlap detection: existing.start < new.end AND existing.end > new.start
        # For open-ended: consider end as infinity

        overlap_conditions = []

        if end_datetime is None:
            # New assignment is ongoing: overlaps with anything that ends after new.start
            overlap_conditions.append(
                {
                    "$or": [
                        {"end_datetime": None},  # Other is also ongoing
                        {
                            "end_datetime": {"$gt": start_datetime}
                        },  # Other ends after we start
                    ]
                }
            )
        else:
            # New assignment has end: overlaps if other starts before we end AND ends after we start
            overlap_conditions.append(
                {
                    "start_datetime": {"$lt": end_datetime},
                }
            )
            overlap_conditions.append(
                {
                    "$or": [
                        {"end_datetime": None},  # Other is ongoing
                        {
                            "end_datetime": {"$gt": start_datetime}
                        },  # Other ends after we start
                    ]
                }
            )

        if overlap_conditions:
            query["$and"] = overlap_conditions

        return query
