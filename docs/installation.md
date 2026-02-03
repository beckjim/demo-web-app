# Installation

Detailed installation instructions for different environments.

## System Requirements

| Requirement    | Version | Notes                         |
| -------------- | ------- | ----------------------------- |
| Python         | 3.9+    | 3.11+ recommended             |
| SQLite         | 3.0+    | Bundled with Python           |
| Modern Browser | Latest  | Chrome, Firefox, Safari, Edge |

## Installation Methods

## Method 1: Using uv (Recommended)

`uv` is a fast, modern Python package manager written in Rust.

```bash
# Install uv
pip install uv

# Create virtual environment
uv venv

# Activate virtual environment
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv sync
```

## Method 2: Traditional pip + venv

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Method 3: Docker

```bash
# Build image
docker build -t employee-dialogue .

# Run container
docker run -p 5000:5000 -p 443:443 \
  -e AZURE_AD_CLIENT_SECRET=your_secret \
  -e SECRET_KEY=your_key \
  employee-dialogue
```

Or use Docker Compose:

```bash
docker compose up
```

## Post-Installation Verification

Verify the installation was successful:

```bash
# Activate environment first
uv run python --version

# Check Flask is installed
uv run flask --version

# Run tests
uv run pytest tests/ -v
```

Expected output:
```
Python 3.14.x
Flask 3.1.x
collected 17 items ...
```

## Dependency Management

### Core Dependencies

| Package          | Version | Purpose                         |
| ---------------- | ------- | ------------------------------- |
| Flask            | 3.1.2   | Web framework                   |
| Flask-SQLAlchemy | 3.1.1   | ORM integration                 |
| gunicorn         | 23.0.0  | Production WSGI server          |
| msal             | 1.34.0  | Microsoft authentication        |
| python-dotenv    | 1.2.1   | Environment variable management |
| requests         | 2.32.5  | HTTP library for Graph API      |

### Development Dependencies

- `ruff>=0.6.9` - Code linting and formatting
- `pytest>=8.0.0` - Testing framework
- `pytest-flask>=1.3.0` - Flask testing utilities

### Documentation Dependencies

- `mkdocs>=1.5.0` - Documentation generator
- `mkdocs-material>=9.0.0` - Material theme
- `mkdocstrings[python]>=0.20.0` - Python API documentation

## Updating Dependencies

```bash
# Update to latest
uv sync --upgrade

# Update specific package
uv pip install --upgrade Flask
```

## Troubleshooting Installation

### "ModuleNotFoundError: No module named 'employee_dialogue'"

1. Ensure virtual environment is activated
2. Run `uv sync` (or `pip install -e .`)
3. Restart the application

### Permission denied errors (Linux/macOS)

```bash
chmod +x .venv/bin/activate
```

### SQLite database locked

- Stop the running application
- Delete `app.db` to reset database
- Restart application

## Next Steps

- [Configuration](configuration.md) - Configure environment variables
- [Getting Started](getting-started.md) - Run your first application
- [Development Setup](development/contributing.md) - Set up development environment
