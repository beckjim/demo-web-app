"""Flask demo app to collect, edit, and delete form entries."""

import os
import uuid
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import or_, func
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import msal
import requests

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

CLIENT_ID = "64326e78-7c64-4dd1-98d4-6bcfd6936c29"
TENANT_ID = "b3cd43f7-99bd-4233-8384-6f3a21adeced"
CLIENT_SECRET = os.environ.get("AZURE_AD_CLIENT_SECRET", "")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/auth/redirect"
SCOPES = ["User.Read", "Directory.Read.All"]

database = SQLAlchemy(app)

OBJECTIVE_CHOICES = [
    "Exceeded objective",
    "Achieved objective",
    "Under-achieved objective",
    "Objective is obsolete or was changed",
]

ABILITY_CHOICES = [
    "Exceeds expectations",
    "Meets expectations",
    "Mostly in line",
    "Below expectations",
    "N/A",
]


class Entry(database.Model):  # pylint: disable=too-few-public-methods
    """Simple submission entry model."""

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(120), nullable=False)
    email = database.Column(database.String(120), nullable=False)
    manager_name = database.Column(database.String(120), nullable=True, default="")
    objective_rating = database.Column(database.String(60), nullable=False)
    objective_comment = database.Column(database.Text, nullable=False)
    technical_rating = database.Column(database.String(40), nullable=False)
    project_rating = database.Column(database.String(40), nullable=False)
    methodology_rating = database.Column(database.String(40), nullable=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    updated_at = database.Column(
        database.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class FinalEntry(database.Model):  # pylint: disable=too-few-public-methods
    """Manager-owned final assessment linked to an employee's self assessment."""

    id = database.Column(database.Integer, primary_key=True)
    source_entry_id = database.Column(database.Integer, nullable=False)
    name = database.Column(database.String(120), nullable=False)
    email = database.Column(database.String(120), nullable=False)
    manager_name = database.Column(database.String(120), nullable=False, default="")
    objective_rating = database.Column(database.String(60), nullable=False)
    objective_comment = database.Column(database.Text, nullable=False)
    technical_rating = database.Column(database.String(40), nullable=False)
    project_rating = database.Column(database.String(40), nullable=False)
    methodology_rating = database.Column(database.String(40), nullable=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    updated_at = database.Column(
        database.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


with app.app_context():
    conn = database.engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(entry)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        drop_message = "message" in existing_cols

        if drop_message:
            cursor.execute("ALTER TABLE entry RENAME TO entry_old")
            conn.commit()

        database.create_all()

        cursor.execute("PRAGMA table_info(entry)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        add_cols = [
            ("manager_name", "TEXT", "''"),
            ("objective_rating", "TEXT", "''"),
            ("objective_comment", "TEXT", "''"),
            ("technical_rating", "TEXT", "''"),
            ("project_rating", "TEXT", "''"),
            ("methodology_rating", "TEXT", "''"),
        ]
        for col_name, col_type, default_val in add_cols:
            if col_name not in existing_cols:
                cursor.execute(
                    f"ALTER TABLE entry ADD COLUMN {col_name} {col_type} NOT NULL DEFAULT {default_val}"
                )

        if drop_message:
            cursor.execute(
                """
                INSERT INTO entry (
                    id, name, email, manager_name, objective_rating,
                    objective_comment, technical_rating, project_rating,
                    methodology_rating, created_at, updated_at
                )
                SELECT
                    id, name, email, manager_name, objective_rating,
                    objective_comment, technical_rating, project_rating,
                    methodology_rating, created_at, updated_at
                FROM entry_old
                """
            )
            cursor.execute("DROP TABLE entry_old")
        conn.commit()
    finally:
        conn.close()


def login_required(func):
    """Redirect to login when user session is missing."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def _build_msal_app() -> msal.ConfidentialClientApplication:
    """Create a MSAL client for auth code flow."""

    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET or None,
    )


def _redirect_uri() -> str:
    """Return the absolute redirect URI registered in Azure AD."""

    return url_for("authorized", _external=True)


def _fetch_manager_name(access_token: str) -> str:
    """Return the manager display name from Microsoft Graph if available."""

    if not access_token:
        return ""

    try:
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/manager",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            return (
                data.get("displayName")
                or data.get("mail")
                or data.get("userPrincipalName")
                or ""
            )

        if response.status_code == 404:
            return ""

        app.logger.warning("Manager lookup failed: %s", response.text)
        return ""
    except Exception:  # pylint: disable=broad-except
        app.logger.exception("Error while fetching manager from Graph")
        return ""


@app.route("/")
@login_required
def index():
    """List all entries sorted by creation time."""
    session_user = session.get("user", {})
    name = session_user.get("name", "")
    own_entries = (
        Entry.query.filter(func.lower(Entry.name) == name.lower())
        .order_by(Entry.created_at.desc())
        .all()
        if name
        else []
    )

    managed_entries = (
        Entry.query.filter(Entry.manager_name == name, Entry.name != name)
        .order_by(Entry.created_at.desc())
        .all()
        if name
        else []
    )

    own_entry = own_entries[0] if own_entries else None

    final_entries = (
        FinalEntry.query.filter(FinalEntry.manager_name == name)
        .order_by(FinalEntry.created_at.desc())
        .all()
        if name
        else []
    )

    final_lookup = {entry.source_entry_id: entry for entry in final_entries}

    return render_template(
        "index.html",
        own_entries=own_entries,
        managed_entries=managed_entries,
        objective_choices=OBJECTIVE_CHOICES,
        ability_choices=ABILITY_CHOICES,
        has_own_entry=bool(own_entry),
        current_name=name,
        final_entries=final_entries,
        final_lookup=final_lookup,
    )


@app.route("/entries/new", methods=["GET"])
@login_required
def new_entry():
    """Display the creation form, redirecting to edit if an entry exists."""

    session_user = session.get("user", {})
    name = session_user.get("name", "")

    existing_entry = (
        Entry.query.filter(func.lower(Entry.name) == name.lower()).first()
        if name
        else None
    )
    if existing_entry:
        flash("You already have an entry. Redirected to edit.", "info")
        return redirect(url_for("edit_entry", entry_id=existing_entry.id))

    return render_template(
        "create.html",
        objective_choices=OBJECTIVE_CHOICES,
        ability_choices=ABILITY_CHOICES,
    )


def _validate_choice(value: str, choices: list[str]) -> bool:
    """Return True if value is one of the allowed choices."""

    return value in choices


def _can_access_entry(entry: Entry, session_user: dict) -> bool:
    """Return True if session user owns the entry (manager-only access is denied)."""

    name = (session_user.get("name") or "").lower()
    entry_owner = (entry.name or "").lower()

    return bool(name and entry_owner and name == entry_owner)


def _can_manage_entry(entry: Entry, session_user: dict) -> bool:
    """Return True if session user is the manager for the given entry."""

    session_name = (session_user.get("name") or "").lower()
    manager_name = (entry.manager_name or "").lower()
    return bool(session_name and manager_name and session_name == manager_name)


def _can_manage_final(final_entry: FinalEntry, session_user: dict) -> bool:
    """Return True if session user is the manager of the linked self assessment."""

    session_name = (session_user.get("name") or "").lower()
    manager_name = (final_entry.manager_name or "").lower()
    return bool(session_name and manager_name and session_name == manager_name)


@app.route("/entries", methods=["POST"])
@login_required
def create_entry():
    """Create a new entry from form data."""
    session_user = session.get("user", {})
    name = session_user.get("name", "")
    email = session_user.get("email", "")
    manager_name = session_user.get("manager_name", "").strip()
    objective_rating = request.form.get("objective_rating", "").strip()
    objective_comment = request.form.get("objective_comment", "").strip()
    technical_rating = request.form.get("technical_rating", "").strip()
    project_rating = request.form.get("project_rating", "").strip()
    methodology_rating = request.form.get("methodology_rating", "").strip()

    base_missing = not name or not email
    objective_missing = not objective_rating or not objective_comment
    abilities_missing = (
        not technical_rating or not project_rating or not methodology_rating
    )
    objective_invalid = not _validate_choice(objective_rating, OBJECTIVE_CHOICES)
    abilities_invalid = not all(
        _validate_choice(val, ABILITY_CHOICES)
        for val in (technical_rating, project_rating, methodology_rating)
    )

    if (
        base_missing
        or objective_missing
        or abilities_missing
        or objective_invalid
        or abilities_invalid
    ):
        flash("All fields must be completed with valid options", "error")
        return redirect(url_for("index"))

    existing_entry = (
        Entry.query.filter(func.lower(Entry.name) == name.lower()).first()
        if name
        else None
    )
    if existing_entry:
        flash(
            "You already have a self assessment. Please edit your existing one instead.",
            "error",
        )
        return redirect(url_for("index"))

    entry = Entry(
        name=name,
        email=email,
        manager_name=manager_name,
        objective_rating=objective_rating,
        objective_comment=objective_comment,
        technical_rating=technical_rating,
        project_rating=project_rating,
        methodology_rating=methodology_rating,
    )
    database.session.add(entry)
    database.session.commit()
    flash("Entry created", "success")
    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    """Edit an existing entry."""
    entry = Entry.query.get_or_404(entry_id)

    session_user = session.get("user", {})
    if not _can_access_entry(entry, session_user):
        flash("You are not allowed to access this entry", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = entry.name
        email = entry.email
        manager_name = session_user.get("manager_name") or entry.manager_name
        objective_rating = request.form.get("objective_rating", "").strip()
        objective_comment = request.form.get("objective_comment", "").strip()
        technical_rating = request.form.get("technical_rating", "").strip()
        project_rating = request.form.get("project_rating", "").strip()
        methodology_rating = request.form.get("methodology_rating", "").strip()

        objective_missing = not objective_rating or not objective_comment
        abilities_missing = (
            not technical_rating or not project_rating or not methodology_rating
        )
        objective_invalid = not _validate_choice(objective_rating, OBJECTIVE_CHOICES)
        abilities_invalid = not all(
            _validate_choice(val, ABILITY_CHOICES)
            for val in (technical_rating, project_rating, methodology_rating)
        )

        if (
            objective_missing
            or abilities_missing
            or objective_invalid
            or abilities_invalid
        ):
            flash("All fields must be completed with valid options", "error")
            return redirect(url_for("edit_entry", entry_id=entry_id))

        entry.name = name
        entry.email = email
        entry.manager_name = manager_name
        entry.objective_rating = objective_rating
        entry.objective_comment = objective_comment
        entry.technical_rating = technical_rating
        entry.project_rating = project_rating
        entry.methodology_rating = methodology_rating
        database.session.commit()
        flash("Entry updated", "success")
        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        entry=entry,
        objective_choices=OBJECTIVE_CHOICES,
        ability_choices=ABILITY_CHOICES,
    )


@app.route("/entries/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    """Delete an existing entry."""
    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})
    if not _can_access_entry(entry, session_user):
        flash("You are not allowed to access this entry", "error")
        return redirect(url_for("index"))
    database.session.delete(entry)
    database.session.commit()
    flash("Entry deleted", "success")
    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/finalize", methods=["POST"])
@login_required
def finalize_entry(entry_id):
    """Create a manager-owned final assessment from an employee self assessment."""

    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})
    if not _can_manage_entry(entry, session_user):
        flash("Only the manager can create a final assessment for this entry.", "error")
        return redirect(url_for("index"))

    existing_final = FinalEntry.query.filter_by(source_entry_id=entry.id).first()
    if existing_final:
        flash("A final assessment already exists for this entry.", "info")
        return redirect(url_for("edit_final_entry", final_id=existing_final.id))

    final_entry = FinalEntry(
        source_entry_id=entry.id,
        name=entry.name,
        email=entry.email,
        manager_name=session_user.get("name") or entry.manager_name,
        objective_rating=entry.objective_rating,
        objective_comment=entry.objective_comment,
        technical_rating=entry.technical_rating,
        project_rating=entry.project_rating,
        methodology_rating=entry.methodology_rating,
    )

    database.session.add(final_entry)
    database.session.commit()
    flash("Final assessment created from managed self assessment.", "success")
    return redirect(url_for("edit_final_entry", final_id=final_entry.id))


@app.route("/final_entries/<int:final_id>/edit", methods=["GET", "POST"])
@login_required
def edit_final_entry(final_id):
    """Edit a final assessment (manager only)."""

    final_entry = FinalEntry.query.get_or_404(final_id)
    session_user = session.get("user", {})

    if not _can_manage_final(final_entry, session_user):
        flash("You are not allowed to access this final assessment.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        objective_rating = request.form.get("objective_rating", "").strip()
        objective_comment = request.form.get("objective_comment", "").strip()
        technical_rating = request.form.get("technical_rating", "").strip()
        project_rating = request.form.get("project_rating", "").strip()
        methodology_rating = request.form.get("methodology_rating", "").strip()

        objective_missing = not objective_rating or not objective_comment
        abilities_missing = (
            not technical_rating or not project_rating or not methodology_rating
        )
        objective_invalid = not _validate_choice(objective_rating, OBJECTIVE_CHOICES)
        abilities_invalid = not all(
            _validate_choice(val, ABILITY_CHOICES)
            for val in (technical_rating, project_rating, methodology_rating)
        )

        if (
            objective_missing
            or abilities_missing
            or objective_invalid
            or abilities_invalid
        ):
            flash("All fields must be completed with valid options", "error")
            return redirect(url_for("edit_final_entry", final_id=final_id))

        final_entry.manager_name = session_user.get("name") or final_entry.manager_name
        final_entry.objective_rating = objective_rating
        final_entry.objective_comment = objective_comment
        final_entry.technical_rating = technical_rating
        final_entry.project_rating = project_rating
        final_entry.methodology_rating = methodology_rating
        database.session.commit()
        flash("Final assessment updated", "success")
        return redirect(url_for("index"))

    return render_template(
        "final_edit.html",
        entry=final_entry,
        objective_choices=OBJECTIVE_CHOICES,
        ability_choices=ABILITY_CHOICES,
    )


@app.route("/login")
def login():
    """Start Microsoft sign-in by redirecting to Azure AD."""

    if not CLIENT_SECRET:
        flash("AZURE_AD_CLIENT_SECRET not set; login will fail.", "error")
    session["state"] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        scopes=SCOPES,
        state=session["state"],
        redirect_uri=_redirect_uri(),
    )
    return redirect(auth_url)


@app.route(REDIRECT_PATH)
def authorized():
    """Process the redirect from Azure AD and establish session."""

    state = request.args.get("state")
    if state != session.get("state"):
        flash("State mismatch. Please try signing in again.", "error")
        return redirect(url_for("index"))

    if request.args.get("error"):
        flash(f"Login failed: {request.args.get('error_description')}", "error")
        return redirect(url_for("index"))

    code = request.args.get("code")
    result = _build_msal_app().acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=_redirect_uri(),
    )

    if "error" in result:
        flash(
            f"Login failed: {result.get('error_description', 'Unknown error')}", "error"
        )
        return redirect(url_for("index"))

    claims = result.get("id_token_claims", {})
    access_token = result.get("access_token")
    manager_name = _fetch_manager_name(access_token)
    user_name = claims.get("name")
    user_email = claims.get("preferred_username")

    if not user_name or not manager_name:
        flash(
            "Login failed: missing required profile information (name or manager).",
            "error",
        )
        return redirect(url_for("login"))

    session["user"] = {
        "name": user_name,
        "email": user_email,
        "oid": claims.get("oid"),
        "manager_name": manager_name,
    }
    flash("Signed in with Microsoft 365", "success")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """Clear local session and sign out of Azure AD."""

    session.clear()
    post_logout = url_for("index", _external=True)
    return redirect(
        f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={post_logout}"
    )


if __name__ == "__main__":
    app.run(debug=True)
