---
applyTo: "**/*.py,**/*.js,**/*.ts,**/*.html,**/*.css"
---

# Code Style & Formatting Standards

## Python (Black + Flake8)

### Black Configuration
- Line length: 99 characters
- Target Python version: 3.10+
- Use double quotes for strings

### Flake8 Rules
- Max line length: 99 (match Black)
- Ignore: E203, W503 (Black compatibility)
- Max complexity: 10

### Import Ordering
1. Standard library imports
2. Third-party imports
3. Local application imports
- Separate groups with a blank line
- Alphabetize within groups

```python
# Example
import os
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.repositories import VehicleRepository
from app.models import Vehicle
```

## JavaScript/TypeScript (ESLint)

### ESLint Configuration
- Use eslint:recommended as base
- Enforce consistent semicolons (always)
- Prefer const over let
- No unused variables
- Enforce camelCase for identifiers

### Import Ordering
1. Node built-ins
2. External packages
3. Internal modules
4. Relative imports
- Separate groups with blank lines

## General Formatting
- Indentation: 4 spaces (Python), 2 spaces (JS/HTML/CSS)
- No trailing whitespace
- Files end with a single newline
- Max line length: 88 (Python), 100 (JS/TS)

## Pre-commit Hooks
Run formatters before committing:
- Python: `black . && flake8`
- JavaScript: `eslint --fix .`
