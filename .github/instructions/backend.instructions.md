---
applyTo: "**/backend/**,**/api/**,**/*.py"
---

# Backend Development Standards

## Architecture
- Follow Domain-Driven Design (DDD)
- Use Repository pattern for data access
- Use pymongo (NOT motor) for database access

## API Design (REST Conventions)

### URL Structure
Example endpoints:
```
GET    /api/v1/vehicles          # List all vehicles
GET    /api/v1/vehicles/{id}     # Get single vehicle
POST   /api/v1/vehicles          # Create vehicle
PUT    /api/v1/vehicles/{id}     # Full update
PATCH  /api/v1/vehicles/{id}     # Partial update
DELETE /api/v1/vehicles/{id}     # Delete vehicle
```

### Versioning
- Use URL path versioning: `/api/v1/`, `/api/v2/`
- Maintain backward compatibility within a version
- Document breaking changes when incrementing versions

### HTTP Status Codes
| Status | Usage |
|--------|-------|
| 200 | Successful GET, PUT, PATCH, DELETE |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE (no content) |
| 400 | Bad request / validation error |
| 401 | Unauthorized (missing/invalid auth) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable entity |
| 500 | Internal server error |

### Response Formats

**Success Response:**
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2026-01-28T10:30:00Z",
    "request_id": "req_xyz123",
    "correlation_id": "corr_abc123"
  }
}
```

**Error Response:**
- 400: Bad Request / Invalid input
- 401: Unauthorized (missing/invalid auth)
- 403: Forbidden (insufficient permissions)
- 404: Resource not found
- 409: Business rule conflict (e.g., already assigned, active assignments)
- 422: Unprocessable Entity (validation errors with per-field `details`)
- 500: Server error
- 503: Service temporarily unavailable

Error format:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": [{ "code": "FIELD_CODE", "message": "detail message" }]
    }
  },
  "meta": {
    "timestamp": "2026-01-28T10:30:00Z",
    "request_id": "req_xyz123",
    "correlation_id": "corr_abc123"
  }
}
```
- Use UPPER_SNAKE_CASE for `error.code` (e.g., `VEHICLE_NOT_FOUND`, `DUPLICATE_PLATE`, `DRIVER_HAS_ACTIVE_ASSIGNMENTS`).
- Validation errors should return **422 Unprocessable Entity** and include per-field `details`.
- Do not include stack traces in API responses.


### Pagination Response Format
```json
{
  "success": true,
  "data": [],
  "pagination": {
    "total": 100,
    "limit": 10,
    "skip": 0,
    "has_more": true
  },
  "meta": {
    "timestamp": "2026-01-28T10:30:00Z",
    "request_id": "req_xyz123",
    "correlation_id": "corr_abc123"
  }
}
```

## Dependency Injection

### Pattern
Use FastAPI's `Depends()` for dependency injection:

```python
from fastapi import Depends
from typing import Annotated

# Define dependency
def get_db():
    client = MongoClient(settings.MONGODB_URI)
    try:
        yield client[settings.DATABASE_NAME]
    finally:
        client.close()

def get_vehicle_repository(
    db: Annotated[Database, Depends(get_db)]
) -> VehicleRepository:
    return VehicleRepository(db)

def get_vehicle_service(
    repository: Annotated[VehicleRepository, Depends(get_vehicle_repository)]
) -> VehicleService:
    return VehicleService(repository)

# Use in endpoint
@router.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: str,
    service: Annotated[VehicleService, Depends(get_vehicle_service)]
):
    return service.get_by_id(vehicle_id)
```

### Dependency Hierarchy
```
Endpoint
  └── Service (business logic)
        └── Repository (data access)
              └── Database connection
```

### Testing with Dependencies
Override dependencies in tests:

```python
from fastapi.testclient import TestClient

def get_mock_repository():
    return Mock(spec=VehicleRepository)

app.dependency_overrides[get_vehicle_repository] = get_mock_repository
client = TestClient(app)
```

## Naming Conventions
- Functions: snake_case (`get_vehicle_by_id`)
- Classes: PascalCase (`VehicleRepository`)
- Constants: SCREAMING_SNAKE_CASE (`MAX_PAGE_SIZE`)
- All IDs must be UUID strings

## Project Structure
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── vehicles.py
│   │       └── router.py
│   ├── domain/
│   │   ├── models/
│   │   │   └── vehicle.py
│   │   └── services/
│   │       └── vehicle_service.py
│   ├── infrastructure/
│   │   └── repositories/
│   │       └── vehicle_repository.py
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   └── main.py
└── tests/
```

## Guidelines
 - Type hints required for all function parameters and return types
 - Docstrings required for all modules, classes, and functions using Google-style format
 - All IDs must be UUID strings
 - HTTP 201 for resource creation
 - HTTP 404 with {"detail": "message"} for not found

## What NOT To Do
- NEVER use 'any' type equivalents
- NEVER hardcode credentials
- NEVER put business logic in endpoints
- NEVER access the database directly from endpoints
- NEVER return raw database objects (use DTOs/schemas)
