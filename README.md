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
uv run flask --app app run --debug
```
App will start on http://127.0.0.1:5000.

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
