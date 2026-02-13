 ---
 name: backend-fastapi-skill
 description: Backend API development standards for FastAPI projects.
 Use when creating endpoints, models, or database operations.
 ---

 # Backend Development Standards

 ## Architecture
 - Follow Domain-Driven Design (DDD)
 - Use Repository pattern for data access

 ## Naming Conventions
 - Functions: snake_case (get_vehicle_by_id)
 - Classes: PascalCase (VehicleRepository)
 - Constants: SCREAMING_SNAKE_CASE

 ## What NOT To Do
 - NEVER use 'any' type equivalents
 - NEVER hardcode credentials

## Guidelines
 - Use pymongo (NOT motor) for database access
 - All IDs must be UUID strings
 - HTTP 201 for resource creation
 - HTTP 404 with {"detail": "message"} for not found

## Testing
 - Use pytest with pytest-cov
 - Follow AAA pattern: Arrange, Act, Assert
 - Minimum 90% coverage on business logic
