# Fleet Management System

A full-stack Fleet Management application for managing vehicles, drivers, and assignments.

## Overview

This application provides a web-based interface for fleet operators to:
- Manage vehicle inventory (add, update, deactivate vehicles)
- Manage driver records (add, update, suspend drivers)
- Create and track vehicle-driver assignments
- View real-time dashboard statistics

## Tech Stack

### Backend
- **Python 3.13** with **FastAPI** framework
- **MongoDB 7.0** for data persistence
- **Pydantic v2** for data validation
- **pytest** for testing (251+ unit tests)

### Frontend
- **Vanilla JavaScript** (ES6 modules)
- **CSS3** with custom properties and responsive design
- **Semantic HTML5** with ARIA accessibility attributes

### Infrastructure
- **Docker & Docker Compose** for containerization
- **Nginx** as reverse proxy for frontend

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for running tests locally)

### Running the Application

```bash
# Clone the repository
git clone <repository-url>
cd fleet-management

# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Running Tests

#### Backend Unit Tests
```bash
cd backend
pip install -r requirements.txt
pytest -v
```

#### E2E Tests (requires running services)
```bash
cd e2e
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
.
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints and schemas
│   │   ├── core/           # Configuration, exceptions, logging
│   │   ├── domain/         # Domain models and services
│   │   └── infrastructure/ # Repository implementations
│   ├── tests/              # Unit tests
│   └── requirements.txt
├── frontend/               # Vanilla JS frontend
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript modules
│   └── *.html             # HTML pages
├── e2e/                   # End-to-end tests
│   └── tests/
├── specs/                 # Specifications and planning
│   ├── constitution.md   # Project rules and guidelines
│   ├── spec.md          # Technical specification
│   ├── plan.md          # Implementation plan
│   └── tasks.md         # Task breakdown
├── docker-compose.yml    # Docker orchestration
└── README.md
```

## API Endpoints

### Health
- `GET /api/v1/health` - Health check

### Vehicles
- `GET /api/v1/vehicles` - List vehicles (with filtering)
- `POST /api/v1/vehicles` - Create vehicle
- `GET /api/v1/vehicles/{id}` - Get vehicle by ID
- `PATCH /api/v1/vehicles/{id}` - Update vehicle
- `DELETE /api/v1/vehicles/{id}` - Soft delete vehicle

### Drivers
- `GET /api/v1/drivers` - List drivers (with filtering)
- `POST /api/v1/drivers` - Create driver
- `GET /api/v1/drivers/{id}` - Get driver by ID
- `PATCH /api/v1/drivers/{id}` - Update driver
- `DELETE /api/v1/drivers/{id}` - Soft delete driver

### Assignments
- `GET /api/v1/assignments` - List assignments
- `POST /api/v1/assignments` - Create assignment
- `GET /api/v1/assignments/{id}` - Get assignment by ID
- `PATCH /api/v1/assignments/{id}` - Update assignment
- `POST /api/v1/assignments/{id}/close` - Close assignment

### Statistics
- `GET /api/v1/stats` - Get dashboard statistics

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://mongodb:27017` |
| `DATABASE_NAME` | Database name | `fleet_db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment name | `development` |

## Development

### Code Style
- **Python**: Black formatter (line length 99), Flake8 linting
- **JavaScript**: ESLint
- **Naming**: snake_case for functions, PascalCase for classes

### Testing Guidelines
- Follow AAA pattern (Arrange, Act, Assert)
- Minimum 90% coverage on business logic
- Use mocks for external dependencies

## License

MIT License - See [LICENSE](LICENSE) for details.
