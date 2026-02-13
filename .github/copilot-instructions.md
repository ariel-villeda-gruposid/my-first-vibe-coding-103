 ---
 name: fleet-management-fullstack-app
 description: Fleet Management backend and frontend standards for managing Vehicles, Drivers, and Assignments.
 Use when creating endpoints, models, or database operations.
 ---

# Fleet Management Fullstack App

## Purpose
This skill guides Copilot to assist in building a Fleet Management application with a Python FastAPI backend and a vanilla JavaScript frontend. It covers coding standards, project structure, API design, error handling, logging, and testing practices.
using **Interview-Driven Test-Driven Development (ID-TDD)** and **Spec Driven Development (SDD) + AI Code Generation**.

Copilot MUST:
- Start from functional behavior
- Ask or infer requirements before implementation
- Write tests first
- Implement only what is required to satisfy failing tests

## Naming Conventions
 - Functions: snake_case (get_vehicle_by_id)
 - Classes: PascalCase (VehicleRepository)
 - Constants: SCREAMING_SNAKE_CASE

## Code Formatting
 - Python: Black (line length 99) + Flake8
 - JavaScript: ESLint
 - Run formatters before committing

## Error Handling
 - Use custom exception classes (inherit from AppException)
 - Structured JSON logging with correlation IDs
 - Never expose internal errors to clients

## Testing
 - Use pytest with pytest-cov
 - Follow AAA pattern: Arrange, Act, Assert
 - Minimum 90% coverage on business logic

## Project Structure
```
./
├──.github/instructions/ # SKILL FILES
│ ├── backend-instructions.md
│ ├── frontend-instructions.md
│ ├── code-style.instructions.md
│ └── qa-instructions.md
├── interviews/ # INTERVIEW TRANSCRIPTS
│ ├── interview-backend.md
│ ├── interview-frontend.md
│ └── interview-qa.md
├── specs/ # Spec Driven Development (SDD)
│ ├── constitution.md
│ ├── spec.md
│ ├── plan.md
│ └── tasks.md
├── backend/ # API CODE (Python)
│ ├── app/
│ │ ├── main.py
│ │ ├── models/
│ │ ├── routes/
│ │ └── database.py
│ ├── tests/
│ ├── Dockerfile
│ └── requirements.txt
├── frontend/ # ADMIN INTERFACE
│ ├── index.html
│ ├── css/
│ └── js/
├── e2e/ # E2E TESTS
│ └── tests/
├── docker-compose.yml # DOCKER ORCHESTRATION
├── .env.example # ENV TEMPLATE
└── skill-adherence-report.md # EVALUATION
```

## Related Instructions
 - See `instructions/backend.instructions.md` for API design & dependency injection
 - See `instructions/frontend.instructions.md` for frontend standards
 - See `instructions/code-style.instructions.md` for detailed formatting rules
 - See `instructions/qa.instructions.md` for testing patterns (mocking, fixtures, E2E)
