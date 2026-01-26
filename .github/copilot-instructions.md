## What this app is
- Single Flask app in [app.py](app.py) with SQLite via SQLAlchemy; one table `Entry` holds form submissions including objective/ability ratings and comments.
- Microsoft Entra (Azure AD) login is mandatory for all routes except `/login`, `/logout`, and the auth redirect; session data is placed under `session['user']` with `name`, `email`, `oid`, `manager_name`.
- Manager field is prefetched from Microsoft Graph `/me/manager` using `Directory.Read.All`; failures are silent and treated as optional.

## Running and environment
- Use `uv` workflow: `pip install uv`, `uv venv`, activate, `uv sync`, then `uv run flask --app app run --debug` (see [README.md](README.md)).
- Required secrets: `AZURE_AD_CLIENT_SECRET` (needed for login), `SECRET_KEY` (Flask session). `.env` is supported via `python-dotenv`.
- Database file lives at `app.db` in the repo root; schema auto-creates on startup. Legacy columns are added in-place via PRAGMA/ALTER logic inside `with app.app_context():`.

## Auth flow details
- Constants: `CLIENT_ID` `TENANT_ID` `SCOPES` (`User.Read`, `Directory.Read.All`). Redirect path is `/auth/redirect`; `_redirect_uri()` uses `_external=True` so match your local host/port.
- Login sets a CSRF-like `state` in session and builds the MSAL auth URL. `/auth/redirect` validates state, exchanges code, captures `id_token_claims` and `access_token`, and stores manager name from Graph.
- Logging out clears the session and redirects to the Entra logout endpoint with `post_logout_redirect_uri` back to index.

## Data model and validation
- `Entry` fields: name, email, manager_name, message, objective_rating/comment, technical/project/methodology ratings, timestamps.
- Allowed values are centralized in `OBJECTIVE_CHOICES` and `ABILITY_CHOICES`; both create/edit routes enforce membership and required fields before committing.
- `login_required` decorator guards create/edit/delete/index; reuse it for any new routes requiring auth.

## UI patterns
- Templates in [templates/base.html](templates/base.html), [templates/index.html](templates/index.html), [templates/edit.html](templates/edit.html).
- New submissions use current session user for name/email (readonly). Manager is readonly on edit and optional on create; keep that behavior unless explicitly changing business rules.
- Entries list newest-first by `created_at`; edit/delete are simple links and POST form respectively.

## Adding features safely
- Reuse `_validate_choice` and choice lists when adding new rating inputs; avoid diverging strings to keep validation consistent.
- If expanding the schema, mirror the lightweight migration approach (ALTER TABLE inside app context) or add proper migrations; do not drop the existing `Entry` table.
- For additional Graph calls, respect the existing 5s timeout and catch/ log exceptions rather than failing the request.

## Debugging tips
- Flash messages already surface validation/auth errors; check server logs for Graph warnings (`app.logger.warning/exception`).
- If login fails with `state` mismatch, ensure session persistence and consistent host/port for redirect URI.
- For SQLite issues, delete `app.db` only if data loss is acceptable; the app will recreate it with all columns.
