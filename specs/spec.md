# Project Specification

## Admin Interface (frontend) Requirements
- Dashboard page: Show stats (vehicle count, driver count, active assignments)
- Vehicles page: CRUD table with add/edit/delete modals
- Drivers page: CRUD table with status indicators
- Assignments page: CRUD with driver/vehicle dropdowns

## Backend API Requirements
- Vehicles CRUD
- Drivers CRUD: Create, Read, Update, Delete + status transitions
- Assignments CRUD: Link drivers to vehicles with date ranges
- Statistics endpoint: GET /api/v1/stats with counts and summaries

### Docker Requirements
- Dockerfile for the FastAPI application
- docker-compose.yml with api and mongodb services
- Environment variables for configuration (DB connection, etc.)
- Health check endpoint: GET /health
- Volume for MongoDB data persistence


### Entities

#### Vehicle
Represents a fleet vehicle.

Attributes:
- id: UUID (string)
- plate_number: string (unique, alphanumeric, no whitespace, max length 10)
- model: string
- year: integer (>= 1996)
- type: enum (SEDAN, SUV, TRUCK, VAN)
- fuel_type: enum (GASOLINE, DIESEL, ELECTRIC, HYBRID)
- status: enum (ACTIVE, INACTIVE, MAINTENANCE)
- created_at: datetime (UTC, auto-generated)
- updated_at: datetime (UTC, auto-generated on create and set to current UTC on every update)

Rules:
- Plate number must be unique (case-insensitive, whitespace-trimmed) and stored normalized (uppercase).
- `plate_number` must be alphanumeric with no whitespace and length <= 10. Leading/trailing whitespace must be trimmed on all string attributes.
- INACTIVE or MAINTENANCE vehicles cannot be assigned. To change to INACTIVE or MAINTENANCE, a vehicle must have no active assignments; assigned vehicles must be unassigned first.
- Only soft deletes are permitted. Deletion is allowed only when the vehicle is not assigned. Reusing a plate requires reactivating the existing soft-deleted vehicle record and updating other fields instead of creating a new record.
- Partial updates must not set omitted required fields to null.
- `updated_at` is auto-generated on create and set to current UTC on every update.
- Concurrency conflicts are detected using `ETag` / `If-Match` and return `409 CONCURRENCY_CONFLICT` on mismatch.

---

#### Driver
Represents a person authorized to operate vehicles.

Attributes:
- id: UUID (string)
- name: string
- license_number: string (unique, alphanumeric)
- contact_number: string (validated phone number format)
- status: enum (ACTIVE, SUSPENDED)
- created_at: datetime (UTC, auto-generated)
- updated_at: datetime (UTC, auto-generated on create and set to current UTC on every update)

Rules:
- SUSPENDED drivers cannot receive assignments.
- `license_number` must be unique (case-insensitive, whitespace-trimmed) and alphanumeric. Reuse of a `license_number` must reactivate the existing deactivated driver record instead of creating a new one.
- Trim leading/trailing whitespace on all string attributes; store normalized values when applicable.
- To suspend or soft-delete a driver, they must have no active assignments; attempts to do so must return `409 DRIVER_HAS_ACTIVE_ASSIGNMENTS`.
- `contact_number` must pass phone number validation and be returned as part of validation details on failure (422).
- Partial updates must not set omitted required fields to null.
- Only soft deletes are permitted.
- Concurrency conflicts are detected using `ETag` / `If-Match` and return `409 CONCURRENCY_CONFLICT` on mismatch.
---

#### Assignment
Represents a relationship between a driver and a vehicle for a time period.

Attributes:
- id: UUID (string)
- driver_id: UUID
- vehicle_id: UUID
- start_datetime: datetime (UTC)
- end_datetime: datetime (UTC) | null
- notes: string | null (max 127 characters after trimming trailing whitespace)
- created_at: datetime (UTC, auto-generated)
- updated_at: datetime (UTC, auto-generated on create and set to current UTC on every update)

Rules:
- A driver can only have one active assignment at a time.
- A vehicle can only have one active assignment at a time.
- POST requests must validate `start_datetime <= end_datetime` when `end_datetime` is provided; `end_datetime` may be null for ongoing assignments.
- Foreign keys (`driver_id`, `vehicle_id`) must exist and be valid (404 `DRIVER_NOT_FOUND` / `VEHICLE_NOT_FOUND`).
- Reassigning the same driver and vehicle again must create a new Assignment record (do not reuse old ones). Checking that there is no active assignment is sufficient (active = `end_datetime` is null or >= now).
- `end_datetime` indicates a closed assignment and must be set to close an active assignment.
- If a vehicle or driver is set to INACTIVE or SUSPENDED respectively, any active assignments must be auto-closed (set `end_datetime = now`) by the service that changed the status.
- `end_datetime` can be updated only if the related driver and vehicle remain ACTIVE and the update does not create overlapping assignments for the same driver or vehicle.
- On update, only `notes` and `end_datetime` may be modified; `start_datetime` can be modified only if the new `start_datetime` is <= now.
- On update, validate `end_datetime >= start_datetime` only if `end_datetime` is not null.
- Creating or updating an assignment with a SUSPENDED driver or INACTIVE/MAINTENANCE vehicle is disallowed (`409 DRIVER_SUSPENDED` / `VEHICLE_INACTIVE`).
- Attempting to delete an active assignment will auto-close it (set `end_datetime = now`) and then return `204 No Content` if successful; otherwise return `409` with the appropriate error code.
- `notes` must be trimmed for trailing whitespace and be <= 127 characters; otherwise return `422 VALIDATION_ERROR` with per-field details.
---