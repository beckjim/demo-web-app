# Employee Dialogue

Flask app for performance review self-assessments and manager evaluations with Microsoft 365 authentication.

## Prerequisites
- Python 3.9+
- pip

## Setup (uv)
```bash
pip install uv
uv venv
.venv\Scripts\activate
uv sync
```

Create a .env file (or edit the provided one):
```
AZURE_AD_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=change_me_in_prod
```

## Run
```bash
uv run flask --app employee_dialogue run --debug
```
App will start on http://127.0.0.1:5000.

## Run with Docker Compose
```bash
docker compose -f compose.yml up -d --build web
```

Container startup performs a one-time app import to initialize/migrate SQLite schema before Gunicorn workers are spawned.
After that, `SKIP_DB_INIT=1` is set for worker processes to prevent concurrent schema initialization races.

### Azure AD / Microsoft 365 login
1) In Entra ID, register a web app with redirect URI `http://127.0.0.1:5000/auth/redirect` (or `http://localhost:5000/auth/redirect` and keep the same in code).
2) Create a client secret and set it locally: `set AZURE_AD_CLIENT_SECRET=<your_secret>` (PowerShell: `$env:AZURE_AD_CLIENT_SECRET="..."`).
3) The app uses:
	- Client ID: `64326e78-7c64-4dd1-98d4-6bcfd6936c29`
	- Tenant ID: `b3cd43f7-99bd-4233-8384-6f3a21adeced`
	- Scopes: `User.Read` and `Directory.Read.All` (Directory.Read.All is needed to prefill the manager field via Microsoft Graph and requires admin consent)
4) Start the app and click “Sign in with Microsoft”; after login you’ll return to the app and can use forms.

## Features
- Create entries with name, email, message
- Prefills manager from Microsoft 365 via Graph `/me/manager` (requires Directory.Read.All)
- List entries sorted by latest update
- Edit or delete existing entries
- SQLite database stored at app.db in project root
- Microsoft 365 sign-in required for form access

## Documentation

Comprehensive documentation is available in the `docs/` folder and generated with mkdocs.

### View documentation locally

```bash
# Install mkdocs
pip install mkdocs mkdocs-material

# Start local documentation server
mkdocs serve
```

Documentation will be available at http://localhost:8000

### Documentation structure
- **[Getting Started](docs/getting-started.md)** - Quick 5-step setup guide
- **[Installation](docs/installation.md)** - Three installation methods
- **[Configuration](docs/configuration.md)** - Environment and Azure AD setup
- **[Usage Guides](docs/usage/)** - How to use the application
- **[Architecture](docs/architecture/)** - System design and data model
- **[Development](docs/development/)** - Contributing and testing
- **[API Reference](docs/api.md)** - REST API endpoints
- **[Deployment](docs/deployment.md)** - Production deployment options
- **[FAQ](docs/faq.md)** - Frequently asked questions

See [DOCUMENTATION.md](DOCUMENTATION.md) for full documentation setup guide.

## Testing
The application includes comprehensive unit tests. See [TESTING.md](TESTING.md) for details.

Quick start:
```bash
# Install test dependencies
uv sync --extra dev

# Run tests
uv run pytest
```

## Notes
- `SECRET_KEY` in app.py is for local use; set a secure value in production.
