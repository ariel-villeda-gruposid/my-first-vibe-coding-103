# Implementation Plan

This plan outlines the phased implementation of the Fleet Management application following Spec-Driven Development (SDD) and ID-TDD principles.

---

## Phase 1: Project Foundation & Infrastructure

**Objective:** Establish the development environment, project structure, and core infrastructure.

### Deliverables
- [ ] Docker Compose configuration (MongoDB + Backend + Frontend)
- [ ] Backend project skeleton with FastAPI
- [ ] Core modules: config, dependencies, exceptions, logging
- [ ] Database connection setup (pymongo)
- [ ] Health check endpoint
- [ ] Frontend project skeleton with HTML/CSS/JS structure
- [ ] CI/CD pipeline foundation (optional)

### Success Criteria
- `docker-compose up` starts all services
- Backend responds to health check at `/api/v1/health`
- Frontend serves static files

---

## Phase 2: Vehicle Domain

**Objective:** Implement complete Vehicle CRUD with all business rules.

### Deliverables
- [ ] Vehicle Pydantic models (request/response schemas)
- [ ] Vehicle domain model
- [ ] VehicleRepository (MongoDB operations)
- [ ] VehicleService (business logic)
- [ ] Vehicle API endpoints (GET, POST, PUT, PATCH, DELETE)
- [ ] Validation: plate_number uniqueness, alphanumeric, normalization
- [ ] Soft delete implementation
- [ ] ETag/If-Match concurrency control
- [ ] Pagination, filtering, sorting support
- [ ] Unit tests (90%+ coverage on service layer)
- [ ] Integration tests for API endpoints

### Frontend
- [ ] Vehicles page (vehicles.html)
- [ ] Vehicle list table with status indicators
- [ ] Add/Edit/Delete modals
- [ ] API integration

### Success Criteria
- All Vehicle CRUD operations work via API
- Business rules enforced (status transitions, soft delete)
- Tests pass with required coverage

---

## Phase 3: Driver Domain

**Objective:** Implement complete Driver CRUD with all business rules.

### Deliverables
- [ ] Driver Pydantic models
- [ ] Driver domain model
- [ ] DriverRepository
- [ ] DriverService
- [ ] Driver API endpoints
- [ ] Validation: license_number uniqueness, contact_number format
- [ ] Status transitions (ACTIVE ↔ SUSPENDED)
- [ ] Soft delete with active assignment checks
- [ ] ETag/If-Match concurrency control
- [ ] Unit tests and integration tests

### Frontend
- [ ] Drivers page (drivers.html)
- [ ] Driver list table with status indicators
- [ ] Add/Edit/Delete modals
- [ ] API integration

### Success Criteria
- All Driver CRUD operations work via API
- Cannot suspend/delete driver with active assignments
- Tests pass with required coverage

---

## Phase 4: Assignment Domain

**Objective:** Implement Assignment CRUD linking drivers to vehicles with time periods.

### Deliverables
- [ ] Assignment Pydantic models
- [ ] Assignment domain model
- [ ] AssignmentRepository
- [ ] AssignmentService
- [ ] Assignment API endpoints
- [ ] Foreign key validation (driver_id, vehicle_id existence)
- [ ] Overlap detection (driver/vehicle can have one active assignment)
- [ ] Auto-close logic when driver suspended or vehicle inactive
- [ ] Notes validation (max 127 chars)
- [ ] Unit tests and integration tests

### Frontend
- [ ] Assignments page (assignments.html)
- [ ] Assignment list with driver/vehicle details
- [ ] Create assignment with driver/vehicle dropdowns
- [ ] Close assignment functionality
- [ ] API integration

### Success Criteria
- Assignments correctly link drivers and vehicles
- Business rules enforced (no overlaps, status checks)
- Auto-close works when status changes

---

## Phase 5: Dashboard & Statistics

**Objective:** Implement statistics endpoint and dashboard UI.

### Deliverables
- [ ] Statistics endpoint (GET /api/v1/stats)
  - Vehicle count by status
  - Driver count by status
  - Active assignments count
  - Recent activity summary
- [ ] StatisticsService
- [ ] Dashboard page (index.html)
- [ ] Stats cards/widgets
- [ ] Charts (optional)

### Success Criteria
- Dashboard displays real-time statistics
- API returns accurate counts

---

## Phase 6: E2E Testing & Polish

**Objective:** Complete E2E test suite and final polish.

### Deliverables
- [ ] E2E tests for critical user flows
- [ ] Error handling improvements
- [ ] UI/UX polish
- [ ] Accessibility audit (ARIA labels, keyboard nav)
- [ ] Responsive design verification
- [ ] Documentation updates
- [ ] Performance review

### Success Criteria
- All E2E tests pass
- Application meets accessibility standards
- Responsive on desktop and tablet

---

## Implementation Order

```
Phase 1 (Foundation)
    ↓
Phase 2 (Vehicles) ─────→ runs parallel with frontend
    ↓
Phase 3 (Drivers) ──────→ runs parallel with frontend
    ↓
Phase 4 (Assignments) ──→ requires Phases 2 & 3
    ↓
Phase 5 (Dashboard) ────→ requires Phases 2, 3, 4
    ↓
Phase 6 (E2E & Polish)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| MongoDB connection issues | Use mongomock for unit tests, test containers for integration |
| Assignment overlap complexity | Comprehensive unit tests for edge cases |
| Concurrency conflicts | Clear ETag strategy, optimistic locking tests |
| Frontend complexity without frameworks | Component-based JS modules, reusable utilities |

---

## Estimated Effort

| Phase | Backend | Frontend | Testing |
|-------|---------|----------|---------|
| Phase 1 | 2h | 1h | 0.5h |
| Phase 2 | 4h | 3h | 2h |
| Phase 3 | 3h | 2h | 1.5h |
| Phase 4 | 4h | 3h | 2h |
| Phase 5 | 2h | 2h | 1h |
| Phase 6 | 1h | 2h | 3h |
| **Total** | **16h** | **13h** | **10h** |
