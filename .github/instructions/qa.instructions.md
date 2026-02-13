---
applyTo: "**/tests/**,**/*_test.py,**/test_*.py"
---

# QA & Testing Standards

## Unit Testing Patterns

### Test Structure (AAA Pattern)
```python
def test_create_vehicle_returns_vehicle_with_uuid():
    # Arrange
    repository = Mock(spec=VehicleRepository)
    service = VehicleService(repository)
    vehicle_data = {"make": "Toyota", "model": "Camry"}
    
    # Act
    result = service.create_vehicle(vehicle_data)
    
    # Assert
    assert result.id is not None
    assert result.make == "Toyota"
```

### Fixtures (pytest)
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_repository():
    """Provides a mocked repository for unit tests."""
    repo = Mock(spec=VehicleRepository)
    repo.find_by_id.return_value = None
    return repo

@pytest.fixture
def vehicle_service(mock_repository):
    """Provides a service instance with mocked dependencies."""
    return VehicleService(repository=mock_repository)

@pytest.fixture
def sample_vehicle():
    """Provides a sample vehicle for testing."""
    return Vehicle(
        id="123e4567-e89b-12d3-a456-426614174000",
        make="Toyota",
        model="Camry",
        year=2024
    )
```

### Mocking Guidelines
- Use `unittest.mock.Mock` or `pytest-mock`
- Always specify `spec=` to catch interface mismatches
- Mock at the boundary (repositories, external APIs)
- Don't mock the unit under test

```python
from unittest.mock import Mock, patch

# Mock a dependency
def test_service_calls_repository(mock_repository):
    service = VehicleService(mock_repository)
    service.get_vehicle("uuid-123")
    mock_repository.find_by_id.assert_called_once_with("uuid-123")

# Patch external calls
@patch("app.services.external_api.fetch_data")
def test_external_integration(mock_fetch):
    mock_fetch.return_value = {"status": "ok"}
    result = process_external_data()
    assert result.status == "ok"
```

## Integration / E2E Testing

### API Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client for API integration tests."""
    return TestClient(app)

def test_create_vehicle_endpoint(client):
    # Arrange
    payload = {"make": "Honda", "model": "Civic", "year": 2024}
    
    # Act
    response = client.post("/api/v1/vehicles", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["make"] == "Honda"
    assert "id" in data
```

### Database Integration Tests
```python
import pytest
from pymongo import MongoClient

@pytest.fixture(scope="function")
def test_db():
    """Provides a clean test database for each test."""
    client = MongoClient("mongodb://localhost:27017")
    db = client["test_database"]
    yield db
    # Cleanup after test
    client.drop_database("test_database")

def test_repository_saves_vehicle(test_db):
    repo = VehicleRepository(test_db)
    vehicle = Vehicle(make="Ford", model="Focus")
    
    saved = repo.save(vehicle)
    
    found = repo.find_by_id(saved.id)
    assert found.make == "Ford"
```

### E2E Test Structure
- Place E2E tests in `e2e/` directory
- Use realistic test data
- Test complete user flows
- Include cleanup/teardown

## Test Naming Conventions
- `test_<method>_<scenario>_<expected_result>`
- Examples:
  - `test_create_vehicle_with_valid_data_returns_201`
  - `test_get_vehicle_with_invalid_id_returns_404`
  - `test_delete_vehicle_when_not_found_raises_error`

## Coverage Requirements
- Minimum 90% on business logic (services, domain)
- Minimum 80% on repositories
- 100% on critical paths (auth, payments)

## What NOT To Do
- NEVER test implementation details (private methods)
- NEVER write tests that depend on execution order
- NEVER use production databases for testing
- NEVER mock everything - test real integrations where practical
