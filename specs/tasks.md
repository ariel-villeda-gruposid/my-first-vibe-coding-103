# Task Breakdown

This document contains the detailed task breakdown for implementing the Fleet Management application.
Tasks are organized by phase and follow ID-TDD (Interview-Driven Test-Driven Development) principles.

Legend: `[ ]` Not started | `[~]` In progress | `[x]` Completed

---

## Phase 1: Project Foundation & Infrastructure

### 1.1 Docker & Infrastructure
- [ ] **TASK-001**: Create docker-compose.yml with MongoDB, backend, and frontend services
- [ ] **TASK-002**: Create backend Dockerfile
- [ ] **TASK-003**: Create frontend Dockerfile (nginx for static files)
- [ ] **TASK-004**: Create .env.example with environment variables
- [ ] **TASK-005**: Verify `docker-compose up` starts all services

### 1.2 Backend Foundation
- [ ] **TASK-010**: Initialize backend project structure
  - app/main.py
  - app/core/config.py
  - app/core/dependencies.py
  - app/core/exceptions.py
  - app/core/logging.py
- [ ] **TASK-011**: Create requirements.txt with dependencies
- [ ] **TASK-012**: Configure FastAPI app with CORS and middleware
- [ ] **TASK-013**: Implement MongoDB connection with pymongo
- [ ] **TASK-014**: Create health check endpoint (GET /api/v1/health)
- [ ] **TASK-015**: Implement structured JSON logging with request_id/correlation_id
- [ ] **TASK-016**: Create base exception classes and error handlers
- [ ] **TASK-017**: Write unit tests for config and exceptions

### 1.3 Frontend Foundation
- [ ] **TASK-020**: Create frontend project structure
  - index.html, vehicles.html, drivers.html, assignments.html
  - css/main.css, css/components.css
  - js/main.js, js/api.js
- [ ] **TASK-021**: Implement base layout with navigation
- [ ] **TASK-022**: Create CSS custom properties for theming
- [ ] **TASK-023**: Implement API client module (js/api.js)
- [ ] **TASK-024**: Create reusable modal component
- [ ] **TASK-025**: Create reusable table component

---

## Phase 2: Vehicle Domain

### 2.1 Backend - Vehicle Models
- [ ] **TASK-100**: Define Vehicle domain model (app/domain/models/vehicle.py)
- [ ] **TASK-101**: Define VehicleStatus, VehicleType, FuelType enums
- [ ] **TASK-102**: Create Vehicle Pydantic schemas (request/response)
  - VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListResponse
- [ ] **TASK-103**: Write tests for Vehicle model validation

### 2.2 Backend - Vehicle Repository
- [ ] **TASK-110**: Implement VehicleRepository (app/infrastructure/repositories/vehicle_repository.py)
  - find_all(filters, pagination, sorting)
  - find_by_id(id)
  - find_by_plate(plate_number)
  - create(vehicle)
  - update(id, vehicle)
  - soft_delete(id)
- [ ] **TASK-111**: Implement ETag generation for vehicles
- [ ] **TASK-112**: Write integration tests for VehicleRepository

### 2.3 Backend - Vehicle Service
- [ ] **TASK-120**: Implement VehicleService (app/domain/services/vehicle_service.py)
  - get_all_vehicles(filters, pagination)
  - get_vehicle_by_id(id)
  - create_vehicle(data)
  - update_vehicle(id, data, etag)
  - delete_vehicle(id)
- [ ] **TASK-121**: Implement plate number normalization (uppercase, trim)
- [ ] **TASK-122**: Implement duplicate plate detection (including soft-deleted)
- [ ] **TASK-123**: Implement status transition validation
- [ ] **TASK-124**: Write unit tests for VehicleService (90%+ coverage)

### 2.4 Backend - Vehicle API
- [ ] **TASK-130**: Create vehicle router (app/api/v1/endpoints/vehicles.py)
- [ ] **TASK-131**: Implement GET /api/v1/vehicles (list with pagination/filtering)
- [ ] **TASK-132**: Implement GET /api/v1/vehicles/{id}
- [ ] **TASK-133**: Implement POST /api/v1/vehicles
- [ ] **TASK-134**: Implement PUT /api/v1/vehicles/{id}
- [ ] **TASK-135**: Implement PATCH /api/v1/vehicles/{id}
- [ ] **TASK-136**: Implement DELETE /api/v1/vehicles/{id}
- [ ] **TASK-137**: Add ETag/If-Match headers handling
- [ ] **TASK-138**: Write API integration tests

### 2.5 Frontend - Vehicles Page
- [ ] **TASK-150**: Create vehicles.html page structure
- [ ] **TASK-151**: Implement vehicle list table with sorting
- [ ] **TASK-152**: Implement vehicle status badges
- [ ] **TASK-153**: Create vehicle add modal
- [ ] **TASK-154**: Create vehicle edit modal
- [ ] **TASK-155**: Implement delete confirmation
- [ ] **TASK-156**: Connect to backend API
- [ ] **TASK-157**: Add error handling and loading states

---

## Phase 3: Driver Domain

### 3.1 Backend - Driver Models
- [ ] **TASK-200**: Define Driver domain model
- [ ] **TASK-201**: Define DriverStatus enum
- [ ] **TASK-202**: Create Driver Pydantic schemas
- [ ] **TASK-203**: Implement contact_number validation (flexible format)
- [ ] **TASK-204**: Write tests for Driver model validation

### 3.2 Backend - Driver Repository
- [ ] **TASK-210**: Implement DriverRepository
- [ ] **TASK-211**: Implement license_number uniqueness check
- [ ] **TASK-212**: Write integration tests for DriverRepository

### 3.3 Backend - Driver Service
- [ ] **TASK-220**: Implement DriverService
- [ ] **TASK-221**: Implement license_number normalization
- [ ] **TASK-222**: Implement status transition with assignment check
- [ ] **TASK-223**: Implement soft delete with assignment check
- [ ] **TASK-224**: Write unit tests for DriverService (90%+ coverage)

### 3.4 Backend - Driver API
- [ ] **TASK-230**: Create driver router
- [ ] **TASK-231**: Implement GET /api/v1/drivers
- [ ] **TASK-232**: Implement GET /api/v1/drivers/{id}
- [ ] **TASK-233**: Implement POST /api/v1/drivers
- [ ] **TASK-234**: Implement PUT /api/v1/drivers/{id}
- [ ] **TASK-235**: Implement PATCH /api/v1/drivers/{id}
- [ ] **TASK-236**: Implement DELETE /api/v1/drivers/{id}
- [ ] **TASK-237**: Write API integration tests

### 3.5 Frontend - Drivers Page
- [ ] **TASK-250**: Create drivers.html page structure
- [ ] **TASK-251**: Implement driver list table
- [ ] **TASK-252**: Implement driver status badges
- [ ] **TASK-253**: Create driver add/edit modals
- [ ] **TASK-254**: Implement delete confirmation
- [ ] **TASK-255**: Connect to backend API

---

## Phase 4: Assignment Domain

### 4.1 Backend - Assignment Models
- [ ] **TASK-300**: Define Assignment domain model
- [ ] **TASK-301**: Create Assignment Pydantic schemas
- [ ] **TASK-302**: Implement notes validation (max 127 chars)
- [ ] **TASK-303**: Write tests for Assignment model validation

### 4.2 Backend - Assignment Repository
- [ ] **TASK-310**: Implement AssignmentRepository
- [ ] **TASK-311**: Implement active assignment queries
- [ ] **TASK-312**: Implement overlap detection queries
- [ ] **TASK-313**: Write integration tests

### 4.3 Backend - Assignment Service
- [ ] **TASK-320**: Implement AssignmentService
- [ ] **TASK-321**: Validate driver/vehicle existence and status
- [ ] **TASK-322**: Implement single active assignment rule
- [ ] **TASK-323**: Implement auto-close on status change
- [ ] **TASK-324**: Implement assignment closing logic
- [ ] **TASK-325**: Write unit tests (90%+ coverage)

### 4.4 Backend - Assignment API
- [ ] **TASK-330**: Create assignment router
- [ ] **TASK-331**: Implement GET /api/v1/assignments
- [ ] **TASK-332**: Implement GET /api/v1/assignments/{id}
- [ ] **TASK-333**: Implement POST /api/v1/assignments
- [ ] **TASK-334**: Implement PATCH /api/v1/assignments/{id}
- [ ] **TASK-335**: Implement DELETE /api/v1/assignments/{id}
- [ ] **TASK-336**: Write API integration tests

### 4.5 Frontend - Assignments Page
- [ ] **TASK-350**: Create assignments.html page structure
- [ ] **TASK-351**: Implement assignment list table
- [ ] **TASK-352**: Create assignment form with driver/vehicle dropdowns
- [ ] **TASK-353**: Implement close assignment action
- [ ] **TASK-354**: Connect to backend API

---

## Phase 5: Dashboard & Statistics

### 5.1 Backend - Statistics
- [ ] **TASK-400**: Implement StatisticsService
- [ ] **TASK-401**: Create statistics endpoint (GET /api/v1/stats)
  - vehicle_count_by_status
  - driver_count_by_status
  - active_assignments_count
  - total_assignments_count
- [ ] **TASK-402**: Write tests for statistics

### 5.2 Frontend - Dashboard
- [ ] **TASK-410**: Create dashboard layout (index.html)
- [ ] **TASK-411**: Implement stats cards
- [ ] **TASK-412**: Implement recent activity section (optional)
- [ ] **TASK-413**: Connect to statistics API

---

## Phase 6: E2E Testing & Polish

### 6.1 E2E Tests
- [ ] **TASK-500**: Set up E2E testing framework
- [ ] **TASK-501**: E2E test: Create vehicle flow
- [ ] **TASK-502**: E2E test: Create driver flow
- [ ] **TASK-503**: E2E test: Create and close assignment flow
- [ ] **TASK-504**: E2E test: Dashboard displays correct stats

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

**Phase:** Not Started  
**Next Task:** TASK-001 - Create docker-compose.yml
