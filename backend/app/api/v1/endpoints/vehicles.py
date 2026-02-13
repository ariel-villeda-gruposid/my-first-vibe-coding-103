"""
Vehicle API endpoints.

Implements CRUD operations for vehicles following REST conventions.
"""

from typing import Annotated, Optional

from app.api.responses import PaginatedResponse, Pagination, SuccessResponse
from app.api.v1.schemas.vehicle import (
    VehicleCreate,
    VehiclePatch,
    VehicleResponse,
    VehicleUpdate,
)
from app.core.dependencies import DatabaseDep
from app.core.logging import get_logger
from app.domain.models.vehicle import FuelType, VehicleStatus, VehicleType
from app.domain.services.vehicle_service import VehicleService
from app.infrastructure.repositories.vehicle_repository import VehicleRepository
from fastapi import APIRouter, Depends, Header, Query, Response, status

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])
logger = get_logger(__name__)


def get_vehicle_service(db: DatabaseDep) -> VehicleService:
    """
    Get Vehicle service instance.

    Args:
        db: MongoDB database instance.

    Returns:
        VehicleService instance with repository.
    """
    vehicle_repository = VehicleRepository(db)
    return VehicleService(vehicle_repository=vehicle_repository)


VehicleServiceDep = Annotated[VehicleService, Depends(get_vehicle_service)]


@router.get(
    "",
    response_model=PaginatedResponse[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Vehicles",
    description="Retrieve a paginated list of vehicles with optional filtering.",
)
def list_vehicles(
    service: VehicleServiceDep,
    status_filter: Optional[VehicleStatus] = Query(
        None, alias="status", description="Filter by vehicle status"
    ),
    vehicle_type: Optional[VehicleType] = Query(
        None, alias="type", description="Filter by vehicle type"
    ),
    fuel_type: Optional[FuelType] = Query(
        None, alias="fuel", description="Filter by fuel type"
    ),
    include_deleted: bool = Query(False, description="Include soft-deleted vehicles"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    sort_by: str = Query(
        "updated_at", pattern="^(created_at|updated_at|plate_number|model)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[VehicleResponse]:
    """
    List all vehicles with optional filtering and pagination.

    Returns:
        PaginatedResponse containing list of vehicles.
    """
    vehicles, total = service.get_all_vehicles(
        status=status_filter,
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        include_deleted=include_deleted,
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    vehicle_responses = [VehicleResponse.from_domain(v) for v in vehicles]

    return PaginatedResponse(
        data=vehicle_responses,
        pagination=Pagination(
            total=total,
            limit=limit,
            skip=skip,
            has_more=(skip + len(vehicles)) < total,
        ),
    )


@router.get(
    "/{vehicle_id}",
    response_model=SuccessResponse[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Vehicle",
    description="Retrieve a single vehicle by ID.",
)
def get_vehicle(
    vehicle_id: str,
    service: VehicleServiceDep,
    response: Response,
) -> SuccessResponse[VehicleResponse]:
    """
    Get a vehicle by ID.

    Args:
        vehicle_id: Vehicle UUID string.
        service: Vehicle service instance.
        response: FastAPI response object for setting headers.

    Returns:
        SuccessResponse containing the vehicle.

    Raises:
        NotFoundException: If vehicle is not found.
    """
    vehicle = service.get_vehicle_by_id(vehicle_id)
    etag = service.get_vehicle_etag(vehicle)
    response.headers["ETag"] = etag

    return SuccessResponse(data=VehicleResponse.from_domain(vehicle))


@router.post(
    "",
    response_model=SuccessResponse[VehicleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Vehicle",
    description=(
        "Create a new vehicle. If a soft-deleted vehicle with the same "
        "plate exists, it will be restored."
    ),
)
def create_vehicle(
    payload: VehicleCreate,
    service: VehicleServiceDep,
    response: Response,
) -> SuccessResponse[VehicleResponse]:
    """
    Create a new vehicle.

    Args:
        payload: Vehicle creation data.
        service: Vehicle service instance.
        response: FastAPI response object for setting headers.

    Returns:
        SuccessResponse containing the created vehicle.

    Raises:
        ConflictException: If plate number is already in use.
    """
    vehicle = service.create_vehicle(
        plate_number=payload.plate_number,
        model=payload.model,
        year=payload.year,
        vehicle_type=payload.type,
        fuel_type=payload.fuel_type,
        status=payload.status or VehicleStatus.ACTIVE,
    )

    etag = service.get_vehicle_etag(vehicle)
    response.headers["ETag"] = etag
    response.headers["Location"] = f"/api/v1/vehicles/{vehicle.id}"

    logger.info(f"Created vehicle with ID: {vehicle.id}")

    return SuccessResponse(data=VehicleResponse.from_domain(vehicle))


@router.put(
    "/{vehicle_id}",
    response_model=SuccessResponse[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Vehicle",
    description=(
        "Fully update a vehicle. Requires all fields. "
        "Use If-Match header for concurrency control."
    ),
)
def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    service: VehicleServiceDep,
    response: Response,
    if_match: Optional[str] = Header(None, alias="If-Match"),
) -> SuccessResponse[VehicleResponse]:
    """
    Fully update a vehicle (PUT operation).

    Args:
        vehicle_id: Vehicle UUID to update.
        payload: Full vehicle data.
        service: Vehicle service instance.
        response: FastAPI response object for setting headers.
        if_match: ETag for concurrency control.

    Returns:
        SuccessResponse containing the updated vehicle.

    Raises:
        NotFoundException: If vehicle is not found.
        ConflictException: If plate number conflicts or status change is invalid.
        ConcurrencyException: If ETag doesn't match.
    """
    vehicle = service.update_vehicle(
        vehicle_id=vehicle_id,
        plate_number=payload.plate_number,
        model=payload.model,
        year=payload.year,
        vehicle_type=payload.type,
        fuel_type=payload.fuel_type,
        status=payload.status,
        etag=if_match,
    )

    etag = service.get_vehicle_etag(vehicle)
    response.headers["ETag"] = etag

    logger.info(f"Updated vehicle with ID: {vehicle_id}")

    return SuccessResponse(data=VehicleResponse.from_domain(vehicle))


@router.patch(
    "/{vehicle_id}",
    response_model=SuccessResponse[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="Partial Update Vehicle",
    description=(
        "Partially update a vehicle. Only provided fields are updated. "
        "Use If-Match header for concurrency control."
    ),
)
def patch_vehicle(
    vehicle_id: str,
    payload: VehiclePatch,
    service: VehicleServiceDep,
    response: Response,
    if_match: Optional[str] = Header(None, alias="If-Match"),
) -> SuccessResponse[VehicleResponse]:
    """
    Partially update a vehicle (PATCH operation).

    Args:
        vehicle_id: Vehicle UUID to update.
        payload: Partial vehicle data.
        service: Vehicle service instance.
        response: FastAPI response object for setting headers.
        if_match: ETag for concurrency control.

    Returns:
        SuccessResponse containing the updated vehicle.

    Raises:
        NotFoundException: If vehicle is not found.
        ConflictException: If plate number conflicts or status change is invalid.
        ConcurrencyException: If ETag doesn't match.
    """
    vehicle = service.patch_vehicle(
        vehicle_id=vehicle_id,
        plate_number=payload.plate_number,
        model=payload.model,
        year=payload.year,
        vehicle_type=payload.type,
        fuel_type=payload.fuel_type,
        status=payload.status,
        etag=if_match,
    )

    etag = service.get_vehicle_etag(vehicle)
    response.headers["ETag"] = etag

    logger.info(f"Patched vehicle with ID: {vehicle_id}")

    return SuccessResponse(data=VehicleResponse.from_domain(vehicle))


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Vehicle",
    description="Soft delete a vehicle. Cannot delete vehicles with active assignments.",
)
def delete_vehicle(
    vehicle_id: str,
    service: VehicleServiceDep,
) -> None:
    """
    Soft delete a vehicle.

    Args:
        vehicle_id: Vehicle UUID to delete.
        service: Vehicle service instance.

    Returns:
        No content on success.

    Raises:
        NotFoundException: If vehicle is not found.
        ConflictException: If vehicle has active assignments.
    """
    service.delete_vehicle(vehicle_id)
    logger.info(f"Soft-deleted vehicle with ID: {vehicle_id}")


@router.get(
    "/stats/by-status",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Vehicle Statistics by Status",
    description="Get count of vehicles grouped by status.",
)
def get_vehicle_stats(
    service: VehicleServiceDep,
) -> SuccessResponse[dict]:
    """
    Get vehicle statistics grouped by status.

    Returns:
        SuccessResponse containing status counts.
    """
    counts = service.get_vehicle_counts_by_status()
    return SuccessResponse(data=counts)
