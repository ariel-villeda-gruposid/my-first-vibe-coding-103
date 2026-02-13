---
applyTo: "**/frontend/**"
---

# Frontend Development Standards

## Technology Stack
- Vanilla HTML/CSS/JavaScript (no framework)
- Styled Components for component-based styling

## File Structure

```
frontend/
├── index.html # Dashboard
├── vehicles.html # Vehicles CRUD
├── drivers.html # Drivers CRUD
├── assignments.html # Assignments CRUD
├── css/
│ ├── main.css # Global styles, CSS custom properties
│ ├── components.css # Reusable component styles
│ └── pages/ # Page-specific styles
└── js/
├── main.js # Shared utilities, API client
├── components/ # Reusable JS components
└── pages/ # Page-specific 
```

## Naming Conventions
- Files: kebab-case (user-profile.js, main-header.css)
- Functions: camelCase (getUserData, handleSubmit)
- Constants: SCREAMING_SNAKE_CASE
- CSS Classes: kebab-case (btn-primary, card-header)
- IDs: camelCase (mainContent, userForm)

## HTML Guidelines
- Use semantic HTML5 elements (header, nav, main, section, article, footer)
- Always include alt attributes for images
- Use data-* attributes for JavaScript hooks
- Maintain proper heading hierarchy (h1 → h2 → h3)

## CSS Guidelines
- Mobile-first responsive design
- Use CSS custom properties (variables) for theming
- Prefer flexbox/grid over float layouts
- Component-scoped styles using BEM or namespacing

## JavaScript Guidelines
- Use ES6+ features (const/let, arrow functions, destructuring)
- Modular code with ES modules (import/export)
- No inline event handlers - use addEventListener
- Avoid global variables - use modules

## What NOT To Do
- NEVER use inline styles for production code
- NEVER use var - use const or let
- NEVER manipulate innerHTML with user input (XSS risk)
- NEVER leave console.log in production code
