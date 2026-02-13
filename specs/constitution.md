# Project Constitution

## Admin Interface (frontend) Requirements
- Responsive layout (works on desktop and tablet)
- Accessibility: Keyboard navigation, ARIA labels, proper contrast
- NO FRAMEWORKS: Pure HTML, CSS, JavaScript (ES6+ modules allowed)

## Backend Requirements
- RESTful API using FastAPI
- Python 3.11+ with FastAPI framework
- MongoDB for data persistence
- Docker and Docker Compose for containerization
- pytest for testing with mongomock or test containers
- All services must run via: docker-compose up


## API Design Principles

- RESTful endpoints
- Resource-oriented URLs (versioned under `/api/v1/`)
- Stateless operations
- Clear validation errors with per-field details
- Distinct layers for controllers, services, and data access
- **Pagination**: Large collections support `limit` and `skip` query parameters (MongoDB cursor style). Default `limit` = 50, maximum `limit` = 500.
- **Filtering**: Resources support filtering via query parameters (status, type, etc.). Soft-deleted resources are excluded by default; include them with `?include_deleted=true`.
- **Sorting**: Default sort by `updated_at` descending. Allowed sort fields include `updated_at`, `created_at` (all resources) and `start_datetime`, `end_datetime` for assignments.
- **Error Handling**: Standardized error response format with error codes and `correlation_id` in `meta`.
- **Date/Time Format**: All datetimes use ISO 8601 format with UTC timezone (e.g., `2026-01-28T10:30:00Z`).
- **ID Format**: All entity IDs are UUID v4 strings (e.g., `123e4567-e89b-12d3-a456-426614174000`). Generated manually using `uuid.uuid4()` and stored as strings in MongoDB.
- **Type Validation**: Pydantic v2 schema validation on all requests.

---

## Responses

### Success(2xx)

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

### Error Handling

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

---

## Infrastructure & Operational

- **Authentication**: Bearer JWT (roles/scopes omitted for v1).
- **API Versioning**: URL path versioning using `/api/v1/...` (major-only semantic versions).
- **Concurrency**: Use `ETag` / `If-Match` for conditional updates; on mismatch return `409 CONCURRENCY_CONFLICT`.
- **Soft-delete visibility**: Soft-deleted resources are excluded by default; include them with `?include_deleted=true`.
- **Pagination defaults**: use `limit` + `skip` with default `limit=50` and max `limit=500`. Responses must include `total` and `has_more`.
- **Logging**: Structured JSON logs including `request_id` and `correlation_id`. Default log level `DEBUG` for dev and `INFO` for prod.
- **Rate limiting**: not implemented in-app; to be provided by cloud infrastructure.

---