# Testing

This application includes comprehensive unit tests using pytest.

## Running Tests

To run the tests:

```bash
# Install test dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test class
uv run pytest test_app.py::TestModels -v

# Run specific test
uv run pytest test_app.py::TestModels::test_entry_creation -v
```

## Test Coverage

The test suite covers:

### Model Tests (`TestModels`)
- Entry model creation
- FinalEntry model creation with source_entry_id

### Validation Tests (`TestValidation`)
- Choice validation (objective and ability ratings)
- Entry access permissions
- Entry management permissions

### Route Tests (`TestRoutes`)
- Authentication redirects for protected routes
- Index page access
- Entry creation form access
- Entry creation with validation
- Successful entry creation
- Entry deletion
- Login/logout flows

### Form Validation Tests (`TestFormValidation`)
- Invalid objective rating rejection
- Invalid ability rating rejection

## Test Database

Tests use an in-memory SQLite database (`sqlite:///:memory:`) that is created fresh for each test run and cleaned up automatically. This ensures tests are isolated and don't affect the development database.

## Fixtures

- `client`: Flask test client with in-memory database
- `authenticated_session`: Test client with authenticated user session

## Continuous Integration

To integrate these tests into CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install uv
    uv sync --extra dev
    uv run pytest -v
```
