# E2E Tests for Fleet Management

This directory contains end-to-end tests that verify complete user flows
against the running application.

## Prerequisites

- Docker and Docker Compose installed
- Application services running: `docker compose up -d`

## Running E2E Tests

```bash
# From the project root
cd e2e
pip install -r requirements.txt
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_vehicle_flow.py` - Vehicle CRUD E2E tests
- `test_driver_flow.py` - Driver CRUD E2E tests
- `test_assignment_flow.py` - Assignment creation and closing E2E tests
- `test_dashboard_flow.py` - Dashboard statistics E2E tests

## Environment Variables

- `API_BASE_URL` - Backend API URL (default: http://localhost:8000)
- `FRONTEND_URL` - Frontend URL (default: http://localhost:3000)
