# Building

Build and deployment information for Employee Dialogue.

## Building the Project

### Local Build

```bash
# Clean previous builds
rm -rf dist/ build/

# Build with uv
uv build

# Output
# Successfully built dist/employee_dialogue-0.1.0.tar.gz
# Successfully built dist/employee_dialogue-0.1.0-py3-none-any.whl
```

### Build System

- **Builder:** Hatchling (modern, fast)
- **Format:** Wheel (`.whl`) and Source (`.tar.gz`)
- **Configuration:** `pyproject.toml`

### Artifacts

```
dist/
├── employee_dialogue-0.1.0-py3-none-any.whl  # Binary wheel
└── employee_dialogue-0.1.0.tar.gz            # Source distribution
```

## Docker Build

### Building Docker Image

```bash
# Build image
docker build -t employee-dialogue:latest .

# Build with buildx (multi-platform)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t employee-dialogue:latest .
```

### Using Docker Compose

```bash
# Build and start services
docker compose up --build

# Stop services
docker compose down

# Rebuild without cache
docker compose up --build --no-cache
```

## Installation

### Install from Wheel

```bash
# From local file
pip install dist/employee_dialogue-0.1.0-py3-none-any.whl

# From PyPI (when published)
pip install employee-dialogue
```

### Install from Source

```bash
# From local source
pip install .

# With development dependencies
pip install ".[dev]"
```

## Configuration for Distribution

### pyproject.toml

```toml
[project]
name = "employee-dialogue"
version = "0.1.0"
description = "Performance review application"

[project.optional-dependencies]
dev = ["ruff>=0.6.9", "pytest>=8.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### MANIFEST.in

Controls which files to include:

```
include README.md
include LICENSE
include TESTING.md
recursive-include docs *.md
recursive-include src *.py
recursive-include src *.html
recursive-include src *.css
```

## Publishing

### PyPI Publication

```bash
# Install twine
pip install twine

# Verify build
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### GitHub Release

1. Create git tag
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Create GitHub Release
   - Tag version
   - Release notes
   - Upload `dist/` artifacts

## Deployment

### Production Checklist

- ✅ Update version number
- ✅ Update CHANGELOG
- ✅ Run full test suite
- ✅ Build locally and test
- ✅ Code review
- ✅ Security audit
- ✅ Performance testing
- ✅ Documentation updated

### Environment Setup

```bash
# Production .env
FLASK_ENV=production
SECRET_KEY=<generated-secure-key>
AZURE_AD_CLIENT_SECRET=<from-azure-portal>
DATABASE_URL=sqlite:///app.db
```

### Running in Production

#### With Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 employee_dialogue:app
```

#### With Docker

```bash
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secret \
  -e AZURE_AD_CLIENT_SECRET=your-secret \
  employee-dialogue:latest
```

#### With Docker Compose

```bash
docker compose -f compose.yml up -d
```

## Database Setup

### Initialize Database

The database auto-initializes on first run:

```bash
uv run flask --app employee_dialogue shell
>>> from employee_dialogue import database
>>> database.create_all()
>>> exit()
```

### Database Backup

```bash
# SQLite backup
cp app.db app.db.backup.$(date +%Y%m%d)

# Or use SQLite dump
sqlite3 app.db .dump > app.db.sql
```

### Database Migration

```bash
# Backup first
cp app.db app.db.backup

# Run application
uv run flask --app employee_dialogue run

# Verify new columns created via ALTER TABLE
```

## Monitoring

### Health Check

```bash
# Simple health endpoint
curl http://localhost:5000/login

# Expected: 200 OK or redirect
```

### Logs

```bash
# Docker logs
docker compose logs -f web

# Application logs
tail -f app.log
```

### Performance Monitoring

```python
# In production, add timing middleware
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    elapsed = time.time() - g.start_time
    app.logger.info(f"Request took {elapsed:.3f}s")
    return response
```

## Troubleshooting Builds

### Build fails with missing dependencies

```bash
# Ensure all dependencies in pyproject.toml
uv sync --all-extras

# Rebuild
uv build
```

### Docker build fails

```bash
# Check Dockerfile syntax
docker build --no-cache -t employee-dialogue .

# View build output
docker build -t employee-dialogue . 2>&1 | tail -20
```

### Installation fails

```bash
# Check Python version
python --version  # Should be 3.9+

# Try wheel instead of sdist
pip install --only-binary :all: employee_dialogue
```

## Version Management

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

- `0.1.0` - Initial release
- `0.2.0` - New features
- `0.2.1` - Bug fixes
- `1.0.0` - Production ready

### Update Version

```bash
# In pyproject.toml
[project]
version = "0.2.0"

# In docs/index.md
Version: 0.2.0

# Commit
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
```

## Next Steps

- [Contributing](contributing.md) - Development workflow
- [Testing](testing.md) - Test suite
- [Deployment](../deployment.md) - Production deployment
