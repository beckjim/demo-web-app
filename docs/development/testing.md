# Testing

Guide for testing Employee Dialogue.

## Overview

The project uses **pytest** with **pytest-flask** for comprehensive testing.

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_app.py

# Run specific test class
uv run pytest tests/test_app.py::TestModels

# Run specific test
uv run pytest tests/test_app.py::TestModels::test_entry_creation
```

### Coverage Reports

```bash
# Generate coverage report
uv run pytest tests/ --cov=src/employee_dialogue --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## Test Structure

```
tests/
├── __init__.py
└── test_app.py
    ├── TestModels
    ├── TestValidation
    ├── TestRoutes
    └── TestFormValidation
```

## Test Categories

### 1. Model Tests (`TestModels`)

Test database models and basic functionality.

```python
def test_entry_creation(self, client):
    """Test creating an Entry."""
    with app.app_context():
        entry = Entry(
            name="Jane Doe",
            email="jane@example.com",
            objective_rating="Achieved objective",
            objective_comment="Met all goals",
            technical_rating="Meets expectations",
            # ... other fields
        )
        database.session.add(entry)
        database.session.commit()
        
        retrieved = Entry.query.first()
        assert retrieved.name == "Jane Doe"
```

### 2. Validation Tests (`TestValidation`)

Test validation functions and access control.

```python
def test_validate_choice_valid(self):
    """Test valid choice validation."""
    assert _validate_choice("Achieved objective", OBJECTIVE_CHOICES)

def test_can_access_entry(self):
    """Test entry access control."""
    entry = Entry(name="Jane Doe", ...)
    session_user = {"name": "Jane Doe"}
    assert _can_access_entry(entry, session_user)
```

### 3. Route Tests (`TestRoutes`)

Test HTTP endpoints and user interactions.

```python
def test_index_redirect_without_auth(self, client):
    """Test index redirects without auth."""
    response = client.get("/")
    assert response.status_code == 302

def test_create_entry_success(self, authenticated_client):
    """Test successful entry creation."""
    response = authenticated_client.post(
        "/entries",
        data={
            "objective_rating": "Achieved objective",
            "objective_comment": "Completed objectives",
            # ... other fields
        }
    )
    assert response.status_code == 302
    assert Entry.query.count() == 1
```

### 4. Form Validation Tests (`TestFormValidation`)

Test form data validation.

```python
def test_invalid_objective_rating(self, authenticated_client):
    """Test invalid objective rating is rejected."""
    response = authenticated_client.post(
        "/entries",
        data={
            "objective_rating": "Invalid rating",
            # ... other fields
        }
    )
    assert response.status_code == 302  # Redirect on error
    assert Entry.query.count() == 0
```

## Writing Tests

### Test Fixtures

```python
@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with app.test_client() as client:
        with app.app_context():
            database.create_all()
        yield client
        with app.app_context():
            database.drop_all()

@pytest.fixture
def authenticated_session(client):
    """Create authenticated session."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "name": "Test User",
            "email": "test@example.com",
            "oid": "test-oid",
            "manager_name": "Test Manager",
        }
    return client
```

### Test Pattern

```python
def test_feature_description(self, client):
    """Test description explaining what is tested."""
    # ARRANGE - Set up test data
    test_data = {"key": "value"}
    
    # ACT - Perform the action
    response = client.post("/endpoint", data=test_data)
    
    # ASSERT - Verify the result
    assert response.status_code == 200
    assert "expected text" in response.data.decode()
```

### Assertions

```python
# HTTP responses
assert response.status_code == 200
assert response.status_code in [200, 201]
assert response.is_json

# Data
assert len(data) > 0
assert item in items
assert data == expected

# Database
assert Entry.query.count() == 1
assert database.session.is_active

# Strings
assert "text" in response.data.decode()
assert response.data.decode().startswith("prefix")
```

## Mocking

### Mock External Calls

```python
from unittest.mock import patch, MagicMock

@patch("requests.get")
def test_with_mocked_requests(self, mock_get):
    """Test with mocked requests."""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"displayName": "Manager Name"}
    )
    
    # Test code that calls requests.get
    manager = _fetch_manager_name("token")
    assert manager == "Manager Name"
```

### Mock Database

```python
@patch("employee_dialogue.database.session")
def test_with_mocked_db(self, mock_session):
    """Test with mocked database."""
    mock_session.query.return_value.first.return_value = None
    
    # Test code
    result = Entry.query.first()
    assert result is None
```

## Test Coverage

### Current Coverage

Run coverage report:

```bash
uv run pytest tests/ --cov=src/employee_dialogue --cov-report=term-missing
```

**Target areas:**
- Route handlers - 100%
- Validation functions - 100%
- Models - 95%+
- Templates - N/A (visual testing)

### Improving Coverage

```bash
# Find untested lines
uv run pytest tests/ --cov=src/employee_dialogue --cov-report=term-missing

# Focus on specific file
uv run pytest tests/ --cov=src/employee_dialogue.__init__ --cov-report=term-missing
```

## Continuous Integration

Tests run automatically on:
- ✅ Push to main branch
- ✅ Pull requests
- ✅ Pre-commit hooks

**Configuration:** `.github/workflows/` (GitHub Actions)

## Troubleshooting Tests

### "ModuleNotFoundError"

```bash
# Reinstall package in editable mode
uv pip install -e .
```

### "Database is locked"

```bash
# Use in-memory database in tests (already done)
"sqlite:///:memory:"
```

### "Session errors"

```python
# Ensure app context
with app.app_context():
    # Database operations here
    pass
```

### Tests are slow

```bash
# Run specific tests only
uv run pytest tests/test_app.py::TestModels -v

# Skip slow tests
uv run pytest tests/ -m "not slow"
```

## Best Practices

✅ **Do:**
- Write tests as you code
- Use descriptive test names
- Keep tests independent
- Clean up after tests
- Mock external services
- Test edge cases

❌ **Don't:**
- Test framework code (pytest, Flask)
- Create dependencies between tests
- Use real external services
- Leave test data in database
- Test unrelated functionality
- Write overly complex tests

## Next Steps

- [Contributing](contributing.md) - Development guidelines
- [Building](building.md) - Build and deployment
