"""
Driver API endpoints.

Implements CRUD operations for drivers following REST conventions.
"""

from typing import Annotated, Optional

from app.api.responses import PaginatedResponse, Pagination, SuccessResponse
from app.api.v1.schemas.driver import (
    DriverCreate,
    DriverPatch,
    DriverResponse,
    DriverUpdate,
)
from app.core.dependencies import DatabaseDep
from app.core.logging import get_logger
from app.domain.models.driver import DriverStatus
from app.domain.services.driver_service import DriverService
from app.infrastructure.repositories.driver_repository import DriverRepository
from fastapi import APIRouter, Depends, Header, Query, Response, status

router = APIRouter(prefix="/drivers", tags=["Drivers"])
logger = get_logger(__name__)


def get_driver_service(db: DatabaseDep) -> DriverService:
    """
    Get Driver service instance.

    Args:
        db: MongoDB database instance.

    Returns:
        DriverService instance with repository.
    """
    driver_repository = DriverRepository(db)
    return DriverService(driver_repository=driver_repository)


DriverServiceDep = Annotated[DriverService, Depends(get_driver_service)]


@router.get(
    "",
    response_model=PaginatedResponse[DriverResponse],
    status_code=status.HTTP_200_OK,
    summary="List Drivers",
    description="Retrieve a paginated list of drivers with optional filtering.",
)
def list_drivers(
    service: DriverServiceDep,
    status_filter: Optional[DriverStatus] = Query(
        None, alias="status", description="Filter by driver status"
    ),
    include_deleted: bool = Query(False, description="Include soft-deleted drivers"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    sort_by: str = Query(
        "updated_at", pattern="^(created_at|updated_at|name|license_number)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[DriverResponse]:
    """
    List all drivers with optional filtering and pagination.

    Returns:
        PaginatedResponse containing list of drivers.
    """
    drivers, total = service.get_all_drivers(
        status=status_filter,
        include_deleted=include_deleted,
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    driver_responses = [DriverResponse.from_domain(d) for d in drivers]

    return PaginatedResponse(
        data=driver_responses,
        pagination=Pagination(
            total=total,
            limit=limit,
            skip=skip,
            has_more=(skip + len(drivers)) < total,
        ),
    )


@router.get(
    "/active",
    response_model=PaginatedResponse[DriverResponse],
    status_code=status.HTTP_200_OK,
    summary="List Active Drivers",
    description=(
        "Retrieve a list of active drivers (not deleted, ACTIVE status). "
        "Useful for assignment dropdowns."
    ),
)
def list_active_drivers(
    service: DriverServiceDep,
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
) -> PaginatedResponse[DriverResponse]:
    """
    List all active drivers for assignment dropdowns.

    Returns:
        PaginatedResponse containing list of active drivers.
    """
    drivers, total = service.get_active_drivers(limit=limit, skip=skip)

    driver_responses = [DriverResponse.from_domain(d) for d in drivers]

    return PaginatedResponse(
        data=driver_responses,
        pagination=Pagination(
            total=total,
            limit=limit,
            skip=skip,
            has_more=(skip + len(drivers)) < total,
        ),
    )


@router.get(
    "/stats/by-status",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Driver Statistics by Status",
    description="Get count of drivers grouped by status.",
)
def get_driver_stats(
    service: DriverServiceDep,
) -> SuccessResponse[dict]:
    """
    Get driver statistics grouped by status.

    Returns:
        SuccessResponse containing status counts.
    """
    counts = service.get_driver_counts_by_status()
    return SuccessResponse(data=counts)


@router.get(
    "/{driver_id}",
    response_model=SuccessResponse[DriverResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Driver",
    description="Retrieve a single driver by ID.",
)
def get_driver(
    driver_id: str,
    service: DriverServiceDep,
    response: Response,
) -> SuccessResponse[DriverResponse]:
    """
    Get a driver by ID.

    Args:
        driver_id: Driver UUID string.
        service: Driver service instance.
        response: FastAPI response object for setting headers.

    Returns:
        SuccessResponse containing the driver.

    Raises:
        NotFoundException: If driver is not found.
    """
    driver = service.get_driver_by_id(driver_id)
    etag = service.get_driver_etag(driver)
    response.headers["ETag"] = etag

    return SuccessResponse(data=DriverResponse.from_domain(driver))


@router.post(
    "",
    response_model=SuccessResponse[DriverResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Driver",
    description=(
        "Create a new driver. If a soft-deleted driver with the same "
        "license number exists, it will be restored."
    ),
)
def create_driver(
    payload: DriverCreate,
    service: DriverServiceDep,
    response: Response,
) -> SuccessResponse[DriverResponse]:
    """
    Create a new driver.

    Args:
        payload: Driver creation data.
        service: Driver service instance.
        response: FastAPI response object for setting headers.

    Returns:
        SuccessResponse containing the created driver.

    Raises:
        ConflictException: If license number is already in use.
    """
    driver = service.create_driver(
        name=payload.name,
        license_number=payload.license_number,
        contact_number=payload.contact_number,
        status=payload.status or DriverStatus.ACTIVE,
    )

    etag = service.get_driver_etag(driver)
    response.headers["ETag"] = etag
    response.headers["Location"] = f"/api/v1/drivers/{driver.id}"

    logger.info(f"Created driver with ID: {driver.id}")

    return SuccessResponse(data=DriverResponse.from_domain(driver))


@router.put(
    "/{driver_id}",
    response_model=SuccessResponse[DriverResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Driver",
    description=(
        "Fully update a driver. Requires all fields. "
        "Use If-Match header for concurrency control."
    ),
)
def update_driver(
    driver_id: str,
    payload: DriverUpdate,
    service: DriverServiceDep,
    response: Response,
    if_match: Optional[str] = Header(None, alias="If-Match"),
) -> SuccessResponse[DriverResponse]:
    """
    Fully update a driver (PUT operation).

    Args:
        driver_id: Driver UUID to update.
        payload: Full driver data.
        service: Driver service instance.
        response: FastAPI response object for setting headers.
        if_match: ETag for concurrency control.

    Returns:
        SuccessResponse containing the updated driver.

    Raises:
        NotFoundException: If driver is not found.
        ConflictException: If license number conflicts or status change is invalid.
        ConcurrencyException: If ETag doesn't match.
    """
    driver = service.update_driver(
        driver_id=driver_id,
        name=payload.name,
        license_number=payload.license_number,
        contact_number=payload.contact_number,
        status=payload.status,
        etag=if_match,
    )

    etag = service.get_driver_etag(driver)
    response.headers["ETag"] = etag

    logger.info(f"Updated driver with ID: {driver_id}")

    return SuccessResponse(data=DriverResponse.from_domain(driver))


@router.patch(
    "/{driver_id}",
    response_model=SuccessResponse[DriverResponse],
    status_code=status.HTTP_200_OK,
    summary="Partial Update Driver",
    description=(
        "Partially update a driver. Only provided fields are updated. "
        "Use If-Match header for concurrency control."
    ),
)
def patch_driver(
    driver_id: str,
    payload: DriverPatch,
    service: DriverServiceDep,
    response: Response,
    if_match: Optional[str] = Header(None, alias="If-Match"),
) -> SuccessResponse[DriverResponse]:
    """
    Partially update a driver (PATCH operation).

    Args:
        driver_id: Driver UUID to update.
        payload: Partial driver data.
        service: Driver service instance.
        response: FastAPI response object for setting headers.
        if_match: ETag for concurrency control.

    Returns:
        SuccessResponse containing the updated driver.

    Raises:
        NotFoundException: If driver is not found.
        ConflictException: If license number conflicts or status change is invalid.
        ConcurrencyException: If ETag doesn't match.
    """
    driver = service.patch_driver(
        driver_id=driver_id,
        name=payload.name,
        license_number=payload.license_number,
        contact_number=payload.contact_number,
        status=payload.status,
        etag=if_match,
    )

    etag = service.get_driver_etag(driver)
    response.headers["ETag"] = etag

    logger.info(f"Patched driver with ID: {driver_id}")

    return SuccessResponse(data=DriverResponse.from_domain(driver))


@router.delete(
    "/{driver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Driver",
    description="Soft delete a driver. Cannot delete drivers with active assignments.",
)
def delete_driver(
    driver_id: str,
    service: DriverServiceDep,
) -> None:
    """
    Soft delete a driver.

    Args:
        driver_id: Driver UUID to delete.
        service: Driver service instance.

    Returns:
        No content on success.

    Raises:
        NotFoundException: If driver is not found.
        ConflictException: If driver has active assignments.
    """
    service.delete_driver(driver_id)
    logger.info(f"Soft-deleted driver with ID: {driver_id}")
