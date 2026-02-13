# Task Breakdown

This document contains the detailed task breakdown for implementing the Fleet Management application.
Tasks are organized by phase and follow ID-TDD (Interview-Driven Test-Driven Development) principles.

Legend: `[ ]` Not started | `[~]` In progress | `[x]` Completed

---

## Phase 1: Project Foundation & Infrastructure

### 1.1 Docker & Infrastructure
- [x] **TASK-001**: Create docker-compose.yml with MongoDB, backend, and frontend services
- [x] **TASK-002**: Create backend Dockerfile
- [x] **TASK-003**: Create frontend Dockerfile (nginx for static files)
- [x] **TASK-004**: Create .env.example with environment variables
- [ ] **TASK-005**: Verify `docker-compose up` starts all services

### 1.2 Backend Foundation
- [x] **TASK-010**: Initialize backend project structure
  - app/main.py
  - app/core/config.py
  - app/core/dependencies.py
  - app/core/exceptions.py
  - app/core/logging.py
- [x] **TASK-011**: Create requirements.txt with dependencies
- [x] **TASK-012**: Configure FastAPI app with CORS and middleware
- [x] **TASK-013**: Implement MongoDB connection with pymongo
- [x] **TASK-014**: Create health check endpoint (GET /api/v1/health)
- [x] **TASK-015**: Implement structured JSON logging with request_id/correlation_id
- [x] **TASK-016**: Create base exception classes and error handlers
- [x] **TASK-017**: Write unit tests for config and exceptions

### 1.3 Frontend Foundation
- [x] **TASK-020**: Create frontend project structure
  - index.html, vehicles.html, drivers.html, assignments.html
  - css/main.css, css/components.css
  - js/main.js, js/api.js
- [x] **TASK-021**: Implement base layout with navigation
- [x] **TASK-022**: Create CSS custom properties for theming
- [x] **TASK-023**: Implement API client module (js/api.js)
- [x] **TASK-024**: Create reusable modal component
- [x] **TASK-025**: Create reusable table component

---

## Phase 2: Vehicle Domain

### 2.1 Backend - Vehicle Models
- [x] **TASK-100**: Define Vehicle domain model (app/domain/models/vehicle.py)
- [x] **TASK-101**: Define VehicleStatus, VehicleType, FuelType enums
- [x] **TASK-102**: Create Vehicle Pydantic schemas (request/response)
  - VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListResponse
- [x] **TASK-103**: Write tests for Vehicle model validation

### 2.2 Backend - Vehicle Repository
- [x] **TASK-110**: Implement VehicleRepository (app/infrastructure/repositories/vehicle_repository.py)
  - find_all(filters, pagination, sorting)
  - find_by_id(id)
  - find_by_plate(plate_number)
  - create(vehicle)
  - update(id, vehicle)
  - soft_delete(id)
- [x] **TASK-111**: Implement ETag generation for vehicles
- [x] **TASK-112**: Write integration tests for VehicleRepository

### 2.3 Backend - Vehicle Service
- [x] **TASK-120**: Implement VehicleService (app/domain/services/vehicle_service.py)
  - get_all_vehicles(filters, pagination)
  - get_vehicle_by_id(id)
  - create_vehicle(data)
  - update_vehicle(id, data, etag)
  - delete_vehicle(id)
- [x] **TASK-121**: Implement plate number normalization (uppercase, trim)
- [x] **TASK-122**: Implement duplicate plate detection (including soft-deleted)
- [x] **TASK-123**: Implement status transition validation
- [x] **TASK-124**: Write unit tests for VehicleService (90%+ coverage)

### 2.4 Backend - Vehicle API
- [x] **TASK-130**: Create vehicle router (app/api/v1/endpoints/vehicles.py)
- [x] **TASK-131**: Implement GET /api/v1/vehicles (list with pagination/filtering)
- [x] **TASK-132**: Implement GET /api/v1/vehicles/{id}
- [x] **TASK-133**: Implement POST /api/v1/vehicles
- [x] **TASK-134**: Implement PUT /api/v1/vehicles/{id}
- [x] **TASK-135**: Implement PATCH /api/v1/vehicles/{id}
- [x] **TASK-136**: Implement DELETE /api/v1/vehicles/{id}
- [x] **TASK-137**: Add ETag/If-Match headers handling
- [x] **TASK-138**: Write API integration tests

### 2.5 Frontend - Vehicles Page
- [x] **TASK-150**: Create vehicles.html page structure
- [x] **TASK-151**: Implement vehicle list table with sorting
- [x] **TASK-152**: Implement vehicle status badges
- [x] **TASK-153**: Create vehicle add modal
- [x] **TASK-154**: Create vehicle edit modal
- [x] **TASK-155**: Implement delete confirmation
- [x] **TASK-156**: Connect to backend API
- [x] **TASK-157**: Add error handling and loading states

---

## Phase 3: Driver Domain

### 3.1 Backend - Driver Models
- [x] **TASK-200**: Define Driver domain model
- [x] **TASK-201**: Define DriverStatus enum
- [x] **TASK-202**: Create Driver Pydantic schemas
- [x] **TASK-203**: Implement contact_number validation (flexible format)
- [x] **TASK-204**: Write tests for Driver model validation

### 3.2 Backend - Driver Repository
- [x] **TASK-210**: Implement DriverRepository
- [x] **TASK-211**: Implement license_number uniqueness check
- [x] **TASK-212**: Write integration tests for DriverRepository

### 3.3 Backend - Driver Service
- [x] **TASK-220**: Implement DriverService
- [x] **TASK-221**: Implement license_number normalization
- [x] **TASK-222**: Implement status transition with assignment check
- [x] **TASK-223**: Implement soft delete with assignment check
- [x] **TASK-224**: Write unit tests for DriverService (90%+ coverage)

### 3.4 Backend - Driver API
- [x] **TASK-230**: Create driver router
- [x] **TASK-231**: Implement GET /api/v1/drivers
- [x] **TASK-232**: Implement GET /api/v1/drivers/{id}
- [x] **TASK-233**: Implement POST /api/v1/drivers
- [x] **TASK-234**: Implement PUT /api/v1/drivers/{id}
- [x] **TASK-235**: Implement PATCH /api/v1/drivers/{id}
- [x] **TASK-236**: Implement DELETE /api/v1/drivers/{id}
- [x] **TASK-237**: Write API integration tests

### 3.5 Frontend - Drivers Page
- [x] **TASK-250**: Create drivers.html page structure
- [x] **TASK-251**: Implement driver list table
- [x] **TASK-252**: Implement driver status badges
- [x] **TASK-253**: Create driver add/edit modals
- [x] **TASK-254**: Implement delete confirmation
- [x] **TASK-255**: Connect to backend API

---

## Phase 4: Assignment Domain

### 4.1 Backend - Assignment Models
- [x] **TASK-300**: Define Assignment domain model
- [x] **TASK-301**: Create Assignment Pydantic schemas
- [x] **TASK-302**: Implement notes validation (max 127 chars)
- [x] **TASK-303**: Write tests for Assignment model validation

### 4.2 Backend - Assignment Repository
- [x] **TASK-310**: Implement AssignmentRepository
- [x] **TASK-311**: Implement active assignment queries
- [x] **TASK-312**: Implement overlap detection queries
- [x] **TASK-313**: Write integration tests

### 4.3 Backend - Assignment Service
- [x] **TASK-320**: Implement AssignmentService
- [x] **TASK-321**: Validate driver/vehicle existence and status
- [x] **TASK-322**: Implement single active assignment rule
- [x] **TASK-323**: Implement auto-close on status change
- [x] **TASK-324**: Implement assignment closing logic
- [x] **TASK-325**: Write unit tests (90%+ coverage)

### 4.4 Backend - Assignment API
- [x] **TASK-330**: Create assignment router
- [x] **TASK-331**: Implement GET /api/v1/assignments
- [x] **TASK-332**: Implement GET /api/v1/assignments/{id}
- [x] **TASK-333**: Implement POST /api/v1/assignments
- [x] **TASK-334**: Implement PATCH /api/v1/assignments/{id}
- [x] **TASK-335**: Implement DELETE /api/v1/assignments/{id}
- [x] **TASK-336**: Write API integration tests

### 4.5 Frontend - Assignments Page
- [x] **TASK-350**: Create assignments.html page structure
- [x] **TASK-351**: Implement assignment list table
- [x] **TASK-352**: Create assignment form with driver/vehicle dropdowns
- [x] **TASK-353**: Implement close assignment action
- [x] **TASK-354**: Connect to backend API


---

## Phase 5: Dashboard & Statistics

### 5.1 Backend - Statistics
- [x] **TASK-400**: Implement StatisticsService
- [x] **TASK-401**: Create statistics endpoint (GET /api/v1/stats)
  - vehicle_count_by_status
  - driver_count_by_status
  - active_assignments_count
  - total_assignments_count
- [x] **TASK-402**: Write tests for statistics

### 5.2 Frontend - Dashboard
- [x] **TASK-410**: Create dashboard layout (index.html)
- [x] **TASK-411**: Implement stats cards
- [ ] **TASK-412**: Implement recent activity section (optional)
- [x] **TASK-413**: Connect to statistics API

---

## Phase 6: E2E Testing & Polish

### 6.1 E2E Tests
- [x] **TASK-500**: Set up E2E testing framework
- [x] **TASK-501**: E2E test: Create vehicle flow
- [x] **TASK-502**: E2E test: Create driver flow
- [x] **TASK-503**: E2E test: Create and close assignment flow
- [x] **TASK-504**: E2E test: Dashboard displays correct stats

### 6.2 Polish & Documentation
- [ ] **TASK-510**: Accessibility audit and fixes
- [ ] **TASK-511**: Responsive design verification
- [ ] **TASK-512**: Error handling improvements
- [ ] **TASK-513**: Update README.md with setup instructions
- [ ] **TASK-514**: Final code review and cleanup

---

## Task Dependencies

```
TASK-001 → TASK-010 → TASK-014 (Foundation must be complete first)
TASK-010 → TASK-100 → TASK-110 → TASK-120 → TASK-130 (Vehicle domain)
TASK-010 → TASK-200 → TASK-210 → TASK-220 → TASK-230 (Driver domain)
TASK-130 + TASK-230 → TASK-300 → TASK-310 → TASK-320 → TASK-330 (Assignments need Vehicles & Drivers)
TASK-330 → TASK-400 (Stats need all domains)
TASK-400 → TASK-500 (E2E needs full implementation)
```

---

## Current Status

**Phase:** Phase 6.1 Complete - E2E Tests Done  
**Next Task:** TASK-510 - Accessibility audit and fixes (Optional Polish)
