# Contributing

Guidelines for contributing to Employee Dialogue.

## Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/beckjim/employee-dialogue.git
cd employee-dialogue

# Create virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install with development dependencies
uv sync --all-extras

# Create .env file
cp .env.example .env
# Edit .env with your Azure AD credentials
```

### IDE Setup

**VSCode Extensions Recommended:**
- Python
- Pylance
- Flask
- Thunder Client or REST Client
- Git Graph

**VSCode Settings:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

## Code Style

### Formatting

We use **ruff** for linting and formatting.

```bash
# Check code
uv run ruff check src/ tests/

# Fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Standards

- **Line length:** 100 characters
- **Python version:** 3.9+
- **Import style:** One import per line
- **Type hints:** Recommended for functions

### Code Organization

```python
"""Module docstring."""

# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import flask
from sqlalchemy import Column, String

# Local imports
from employee_dialogue import database

# Constants
CONSTANTS_ARE_UPPERCASE = True

def functions_are_snake_case():
    """Functions follow snake_case."""
    pass

class ClassesArePascalCase:
    """Classes follow PascalCase."""
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/employee_dialogue

# Run specific test
uv run pytest tests/test_app.py::TestModels::test_entry_creation

# Run with verbose output
uv run pytest tests/ -v
```

### Writing Tests

```python
import pytest
from employee_dialogue import app, database, Entry

@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with app.app_client() as client:
        with app.app_context():
            database.create_all()
        yield client
        with app.app_context():
            database.drop_all()

class TestFeature:
    """Test suite for a feature."""
    
    def test_something(self, client):
        """Test description."""
        response = client.get("/")
        assert response.status_code == 200
```

### Test Coverage Target

- **Minimum:** 80%
- **Target:** 90%+
- **Critical paths:** 100%

## Documentation

### Docstring Format

```python
def create_entry():
    """
    Create a new performance review entry.
    
    This function validates form data and creates a new Entry
    in the database.
    
    Raises:
        ValueError: If validation fails
        
    Returns:
        Response: Redirect to dashboard
    """
    pass
```

### Update Documentation

- Edit markdown files in `docs/`
- Run `mkdocs serve` to preview
- Commit changes with code

## Git Workflow

### Branch Naming

```
feature/description              # New feature
fix/issue-description            # Bug fix
docs/documentation-topic         # Documentation
refactor/component-name          # Code refactoring
test/test-description            # Test additions
```

### Commits

```bash
# Good commit message
git commit -m "Add manager feedback form

- Implement FinalEntry model
- Create final_edit.html template
- Add manager validation logic

Closes #123"

# Not good
git commit -m "fixes"
```

### Pull Requests

1. Fork repository (if external contributor)
2. Create feature branch
3. Make changes with tests
4. Run linting and tests
5. Push branch
6. Create Pull Request with description
7. Address review comments
8. Merge when approved

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

### Flask Debug Mode

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
uv run flask run
```

### Debug Database

```python
# Print SQL queries
app.config["SQLALCHEMY_ECHO"] = True

# Inspect database
sqlite3 app.db
sqlite> .schema
sqlite> SELECT * FROM entry;
```

### VSCode Debugger

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "employee_dialogue",
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "args": ["run"],
            "jinja": true,
            "justMyCode": true
        }
    ]
}
```

## Common Tasks

### Adding a New Route

```python
@app.route("/new-route", methods=["GET", "POST"])
@login_required
def new_route():
    """Description of route."""
    session_user = session.get("user", {})
    
    if request.method == "POST":
        # Handle POST
        pass
    
    return render_template("new_route.html", user=session_user)
```

### Adding a Database Field

1. Add to SQLAlchemy model
2. Add migration (ALTER TABLE)
3. Update templates
4. Add tests
5. Document in CHANGELOG

### Adding a Template

1. Create in `src/employee_dialogue/templates/`
2. Follow existing naming convention
3. Extend `base.html`
4. Use Flask template variables
5. Test responsiveness

## Performance

### Optimization Tips

- ✅ Use `func.lower()` for case-insensitive queries
- ✅ Avoid N+1 queries (use eager loading)
- ✅ Cache manager lookups from Graph API
- ✅ Minimize Graph API calls
- ✅ Use pagination for large datasets

### Profiling

```bash
# Profile with cProfile
python -m cProfile -s cumulative -o profile.prof app.py

# Analyze results
python -m pstats profile.prof
```

## Security Checklist

Before submitting code:

- ✅ No hardcoded secrets
- ✅ SQL injection prevention (use ORM)
- ✅ CSRF protection (use session tokens)
- ✅ XSS protection (use Jinja2 escaping)
- ✅ Input validation
- ✅ Access control checks
- ✅ Error messages don't leak info

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit: `git commit -m "Release v0.2.0"`
4. Tag: `git tag v0.2.0`
5. Build: `uv build`
6. Publish documentation

## Getting Help

- 📖 Read [Architecture](../architecture/structure.md)
- 🤝 Check existing issues
- 💬 Create new issue with details
- 📧 Contact maintainers

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Acknowledge good work
- Report issues professionally
