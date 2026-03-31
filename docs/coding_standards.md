# Coding Standards

## Python Standards
- Always use `python3`, never bare `python`
- Always use `pip3 install --break-system-packages`
- Follow PEP 8 style guidelines
- Use type hints where applicable
- Docstrings for all public functions and classes

## Import Standards
- No relative imports in tests
- Import from installed packages or build fresh
- Never import from .patrickignore'd modules
- Use absolute imports for clarity

## Test Standards
- Use descriptive test function names
- One assertion per test when possible
- Setup and teardown through context managers
- Mock external dependencies appropriately
- Follow import-only validation pattern

## Error Handling
- Explicit error handling with specific exceptions
- Meaningful error messages for debugging
- Log errors appropriately with context
- Fail fast on critical errors

## Code Organization
- Single responsibility principle
- Clear separation of concerns
- Modular design with minimal coupling
- Consistent naming conventions

## Documentation Standards
- Clear docstrings for all modules
- Inline comments for complex logic
- README files for major components
- API documentation where applicable

## Security Standards
- Never commit secrets or credentials
- Use environment variables for configuration
- Sanitize user inputs
- Follow secure coding practices

## Performance Guidelines
- Profile code for bottlenecks
- Use appropriate data structures
- Minimize database queries
- Cache results when appropriate
