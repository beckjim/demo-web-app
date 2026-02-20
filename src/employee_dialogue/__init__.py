"""Employee Dialogue - Flask app to collect, edit, and delete performance review entries."""

import os
import uuid

from datetime import datetime
from datetime import timezone
from functools import wraps
from typing import Any
from typing import Callable
from typing import Union
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

import msal
import requests

from dotenv import load_dotenv
from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.wrappers.response import Response

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


def _utc_now() -> datetime:
    """Return current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


try:
    GERMAN_TZ = ZoneInfo("Europe/Berlin")
except ZoneInfoNotFoundError:
    app.logger.warning(
        "Timezone data not available; falling back to UTC. Install tzdata for Europe/Berlin."
    )
    GERMAN_TZ = timezone.utc


def _format_german_time(value: Union[datetime, None]) -> str:
    """Format a datetime in German timezone with offset info."""

    if value is None:
        return "N/A"

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    local_time = value.astimezone(GERMAN_TZ)
    offset = local_time.strftime("%z")
    if offset:
        offset = f"{offset[:3]}:{offset[3:]}"
    return f"{local_time:%Y-%m-%d %H:%M} Europe/Berlin (UTC{offset})"


@app.template_filter("german_time")
def german_time_filter(value: Union[datetime, None]) -> str:
    """Jinja filter for German timezone timestamp formatting."""

    return _format_german_time(value)


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

STATUS_NOT_CREATED = "not_created_yet"
STATUS_CREATED = "created"
STATUS_FINALIZED = "finalized_with_manager"
STATUS_SUBMITTED = "submitted_to_program_manager"
STATUS_APPROVED = "approved_by_program_manager"

STATUS_LABELS = {
    STATUS_NOT_CREATED: "not created yet",
    STATUS_CREATED: "created",
    STATUS_FINALIZED: "finalized with manager",
    STATUS_SUBMITTED: "submitted to program manager",
    STATUS_APPROVED: "approved by program manager",
}

STATUS_TOOLTIPS = {
    STATUS_NOT_CREATED: "The team member has not created a self assessment yet.",
    STATUS_CREATED: "The self assessment is created and waiting for manager finalization.",
    STATUS_FINALIZED: "The manager finalized the assessment and can now submit it to the program manager.",
    STATUS_SUBMITTED: "The finalized assessment was submitted to the program manager and is locked for editing.",
    STATUS_APPROVED: "The program manager approved the submitted assessment. Workflow is complete.",
}

STATUS_CLASSES = {
    STATUS_NOT_CREATED: "status-not-created",
    STATUS_CREATED: "status-created",
    STATUS_FINALIZED: "status-finalized",
    STATUS_SUBMITTED: "status-submitted",
    STATUS_APPROVED: "status-approved",
}


class Entry(database.Model):
    """Simple submission entry model."""

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(120), nullable=False)
    email = database.Column(database.String(120), nullable=False)
    manager_name = database.Column(database.String(120), nullable=True, default="")
    objective_rating = database.Column(database.String(60), nullable=False)
    objective_comment = database.Column(database.Text, nullable=False)
    manager_objective_comment = database.Column(database.Text, nullable=False, default="")
    technical_rating = database.Column(database.String(40), nullable=False)
    project_rating = database.Column(database.String(40), nullable=False)
    methodology_rating = database.Column(database.String(40), nullable=False)
    abilities_comment = database.Column(database.Text, nullable=False, default="")
    manager_abilities_comment = database.Column(database.Text, nullable=False, default="")
    efficiency_collaboration = database.Column(database.String(40), nullable=False, default="")
    efficiency_ownership = database.Column(database.String(40), nullable=False, default="")
    efficiency_resourcefulness = database.Column(database.String(40), nullable=False, default="")
    efficiency_comment = database.Column(database.Text, nullable=False, default="")
    manager_efficiency_comment = database.Column(database.Text, nullable=False, default="")
    conduct_mutual_trust = database.Column(database.String(40), nullable=False, default="")
    conduct_proactivity = database.Column(database.String(40), nullable=False, default="")
    conduct_leadership = database.Column(database.String(40), nullable=False, default="")
    conduct_comment = database.Column(database.Text, nullable=False, default="")
    general_comments = database.Column(database.Text, nullable=False, default="")
    goals_2026 = database.Column(database.Text, nullable=False, default="")
    manager_general_comments = database.Column(database.Text, nullable=False, default="")
    feedback_received = database.Column(database.String(10), nullable=False, default="")
    program_manager_name = database.Column(database.String(120), nullable=False, default="")
    workflow_status = database.Column(
        database.String(40), nullable=False, default=STATUS_CREATED
    )
    created_at = database.Column(database.DateTime, default=_utc_now)
    updated_at = database.Column(database.DateTime, default=_utc_now, onupdate=_utc_now)


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
            ("manager_objective_comment", "TEXT", "''"),
            ("technical_rating", "TEXT", "''"),
            ("project_rating", "TEXT", "''"),
            ("methodology_rating", "TEXT", "''"),
            ("abilities_comment", "TEXT", "''"),
            ("manager_abilities_comment", "TEXT", "''"),
            ("efficiency_collaboration", "TEXT", "''"),
            ("efficiency_ownership", "TEXT", "''"),
            ("efficiency_resourcefulness", "TEXT", "''"),
            ("efficiency_comment", "TEXT", "''"),
            ("manager_efficiency_comment", "TEXT", "''"),
            ("conduct_mutual_trust", "TEXT", "''"),
            ("conduct_proactivity", "TEXT", "''"),
            ("conduct_leadership", "TEXT", "''"),
            ("conduct_comment", "TEXT", "''"),
            ("general_comments", "TEXT", "''"),
            ("goals_2026", "TEXT", "''"),
            ("manager_general_comments", "TEXT", "''"),
            ("feedback_received", "TEXT", "''"),
            ("program_manager_name", "TEXT", "''"),
            ("workflow_status", "TEXT", f"'{STATUS_CREATED}'"),
        ]
        for col_name, col_type, default_val in add_cols:
            if col_name not in existing_cols:
                cursor.execute(
                    "ALTER TABLE entry ADD COLUMN "
                    f"{col_name} {col_type} NOT NULL DEFAULT {default_val}"
                )

        cursor.execute(
            "UPDATE entry SET workflow_status = ? WHERE workflow_status IS NULL OR workflow_status = ''",
            (STATUS_CREATED,),
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


def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Redirect to login when user session is missing."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def _graph_display_name(data: Any) -> str:
    """Return a user-friendly name from a Microsoft Graph user payload."""

    if not isinstance(data, dict):
        return ""
    return data.get("displayName") or data.get("mail") or data.get("userPrincipalName") or ""


def _graph_get(url: str, access_token: str) -> Union[requests.Response, None]:
    """Issue a Microsoft Graph GET request with standard headers and timeout."""

    try:
        return requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
    except Exception:  # pylint: disable=broad-except
        app.logger.exception("Error while calling Graph URL: %s", url)
        return None


def _fetch_program_manager_name(access_token: str, manager_id: Any, manager_name: str) -> str:
    """Walk up the manager chain and return the organization-head display name."""

    current_manager_id = manager_id if isinstance(manager_id, str) else ""
    program_manager_name = manager_name
    visited_ids = set()

    while current_manager_id and current_manager_id not in visited_ids:
        visited_ids.add(current_manager_id)
        hierarchy_response = _graph_get(
            f"https://graph.microsoft.com/v1.0/users/{current_manager_id}/manager",
            access_token,
        )

        if hierarchy_response is None:
            break

        if hierarchy_response.status_code == 404:
            break

        if hierarchy_response.status_code != 200:
            app.logger.warning("Program manager lookup failed: %s", hierarchy_response.text)
            break

        hierarchy_data = hierarchy_response.json()
        higher_manager_name = _graph_display_name(hierarchy_data)
        if higher_manager_name:
            program_manager_name = higher_manager_name

        next_manager_id = hierarchy_data.get("id") if isinstance(hierarchy_data, dict) else None
        if not isinstance(next_manager_id, str):
            break
        current_manager_id = next_manager_id

    return program_manager_name


def _fetch_manager_hierarchy(access_token: str) -> tuple[str, str]:
    """Return direct manager and organization-head names from Microsoft Graph."""

    if not access_token:
        return "", ""

    response = _graph_get("https://graph.microsoft.com/v1.0/me/manager", access_token)
    if response is None:
        return "", ""

    if response.status_code == 404:
        return "", ""

    if response.status_code != 200:
        app.logger.warning("Manager lookup failed: %s", response.text)
        return "", ""

    data = response.json()
    manager_name = _graph_display_name(data)
    manager_id = data.get("id") if isinstance(data, dict) else None
    program_manager_name = _fetch_program_manager_name(access_token, manager_id, manager_name)
    return manager_name, program_manager_name


def _fetch_direct_reports(access_token: str) -> list[dict[str, str]]:
    """Return direct reports for the current user from Microsoft Graph."""

    if not access_token:
        return []

    reports: list[dict[str, str]] = []
    next_url = (
        "https://graph.microsoft.com/v1.0/me/directReports"
        "?$select=id,displayName,mail,userPrincipalName"
    )

    while next_url:
        response = _graph_get(next_url, access_token)
        if response is None:
            return reports

        if response.status_code == 404:
            return []

        if response.status_code != 200:
            app.logger.warning("Direct reports lookup failed: %s", response.text)
            return reports

        data = response.json()
        values = data.get("value", []) if isinstance(data, dict) else []

        for item in values:
            if not isinstance(item, dict):
                continue
            display_name = _graph_display_name(item)
            if not display_name:
                continue
            reports.append(
                {
                    "oid": item.get("id") or "",
                    "name": display_name,
                    "email": item.get("mail") or item.get("userPrincipalName") or "",
                }
            )

        next_url = data.get("@odata.nextLink", "") if isinstance(data, dict) else ""

    return reports


def _managed_status(entry: Union[Entry, None]) -> str:
    """Return status code for a managed self-assessment lifecycle."""

    if entry is None:
        return STATUS_NOT_CREATED

    candidate = (entry.workflow_status or "").strip()
    if candidate in STATUS_LABELS:
        return candidate
    return STATUS_CREATED


def _managed_timestamp(entry: Union[Entry, None]) -> str:
    """Return a display timestamp for managed row state changes."""

    if entry and entry.updated_at:
        return _format_german_time(entry.updated_at)
    return "N/A"


@app.route("/")
@login_required
def index() -> str:
    """List all entries sorted by creation time."""
    session_user = session.get("user", {})
    name = session_user.get("name", "")
    raw_refreshed_at = session_user.get("direct_reports_refreshed_at")
    if isinstance(raw_refreshed_at, str):
        try:
            team_refreshed_at = _format_german_time(datetime.fromisoformat(raw_refreshed_at))
        except ValueError:
            team_refreshed_at = raw_refreshed_at
    else:
        team_refreshed_at = "N/A"
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
    direct_reports = session_user.get("direct_reports", [])
    if not isinstance(direct_reports, list):
        direct_reports = []

    own_status_code = _managed_status(own_entry)
    own_status_label = STATUS_LABELS.get(own_status_code, STATUS_LABELS[STATUS_CREATED])
    own_status_tooltip = STATUS_TOOLTIPS.get(own_status_code, "")
    own_timestamp_label = _managed_timestamp(own_entry)

    managed_by_email = {
        (entry.email or "").lower(): entry for entry in managed_entries if (entry.email or "").strip()
    }
    managed_by_name = {
        (entry.name or "").lower(): entry for entry in managed_entries if (entry.name or "").strip()
    }

    managed_rows: list[dict[str, Any]] = []
    seen_entry_ids: set[int] = set()

    for report in direct_reports:
        report_name = report.get("name", "")
        report_email = report.get("email", "")
        report_oid = report.get("oid", "")
        entry = managed_by_email.get(report_email.lower()) or managed_by_name.get(report_name.lower())
        status_code = _managed_status(entry)
        if entry:
            seen_entry_ids.add(entry.id)

        managed_rows.append(
            {
                "member_name": report_name,
                "member_email": report_email,
                "member_oid": report_oid,
                "entry": entry,
                "status_code": status_code,
                "status_label": STATUS_LABELS.get(status_code, STATUS_LABELS[STATUS_CREATED]),
                "status_tooltip": STATUS_TOOLTIPS.get(status_code, ""),
                "status_class": STATUS_CLASSES.get(status_code, "status-created"),
                "timestamp_label": _managed_timestamp(entry),
            }
        )

    for entry in managed_entries:
        if entry.id in seen_entry_ids:
            continue
        status_code = _managed_status(entry)
        managed_rows.append(
            {
                "member_name": entry.name,
                "member_email": entry.email,
                "member_oid": "",
                "entry": entry,
                "status_code": status_code,
                "status_label": STATUS_LABELS.get(status_code, STATUS_LABELS[STATUS_CREATED]),
                "status_tooltip": STATUS_TOOLTIPS.get(status_code, ""),
                "status_class": STATUS_CLASSES.get(status_code, "status-created"),
                "timestamp_label": _managed_timestamp(entry),
            }
        )

    managed_rows.sort(key=lambda row: (row.get("member_name") or "").lower())

    return render_template(
        "index.html",
        own_entries=own_entries,
        managed_entries=managed_entries,
        managed_rows=managed_rows,
        objective_choices=OBJECTIVE_CHOICES,
        ability_choices=ABILITY_CHOICES,
        has_own_entry=bool(own_entry),
        current_name=name,
        team_refreshed_at=team_refreshed_at,
        own_status_code=own_status_code,
        own_status_label=own_status_label,
        own_status_tooltip=own_status_tooltip,
        own_timestamp_label=own_timestamp_label,
        own_status_class=STATUS_CLASSES.get(own_status_code, "status-created"),
        status_not_created=STATUS_NOT_CREATED,
        status_created=STATUS_CREATED,
        status_finalized=STATUS_FINALIZED,
        status_submitted=STATUS_SUBMITTED,
        status_approved=STATUS_APPROVED,
        status_classes=STATUS_CLASSES,
    )


@app.route("/team/refresh", methods=["POST"])
@login_required
def refresh_team_members() -> Response:
    """Refresh managed team members by re-running sign-in flow."""

    session["post_login_redirect"] = url_for("index")
    flash("Refreshing team members from Microsoft Entra...", "info")
    return redirect(url_for("login", next=url_for("index")))


@app.route("/entries/new", methods=["GET"])
@login_required
def new_entry() -> Union[str, Response]:
    """Display the creation form, redirecting to edit if an entry exists."""

    session_user = session.get("user", {})
    name = session_user.get("name", "")

    existing_entry = (
        Entry.query.filter(func.lower(Entry.name) == name.lower()).first() if name else None
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


def _can_access_entry(entry: Entry, session_user: dict[str, Any]) -> bool:
    """Return True if session user owns the entry (manager-only access is denied)."""

    name = (session_user.get("name") or "").lower()
    entry_owner = (entry.name or "").lower()

    return bool(name and entry_owner and name == entry_owner)


def _can_manage_entry(entry: Entry, session_user: dict[str, Any]) -> bool:
    """Return True if session user is the manager for the given entry."""

    session_name = (session_user.get("name") or "").lower()
    manager_name = (entry.manager_name or "").lower()
    return bool(session_name and manager_name and session_name == manager_name)


def _can_approve_entry(entry: Entry, session_user: dict[str, Any]) -> bool:
    """Return True if session user is the designated program manager."""

    session_name = (session_user.get("name") or "").lower()
    program_manager_name = (entry.program_manager_name or "").lower()
    return bool(session_name and program_manager_name and session_name == program_manager_name)


@app.route("/entries", methods=["POST"])
@login_required
def create_entry() -> Response:
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
    abilities_comment = request.form.get("abilities_comment", "").strip()
    efficiency_collaboration = request.form.get("efficiency_collaboration", "").strip()
    efficiency_ownership = request.form.get("efficiency_ownership", "").strip()
    efficiency_resourcefulness = request.form.get("efficiency_resourcefulness", "").strip()
    efficiency_comment = request.form.get("efficiency_comment", "").strip()
    conduct_mutual_trust = request.form.get("conduct_mutual_trust", "").strip()
    conduct_proactivity = request.form.get("conduct_proactivity", "").strip()
    conduct_leadership = request.form.get("conduct_leadership", "").strip()
    conduct_comment = request.form.get("conduct_comment", "").strip()
    general_comments = request.form.get("general_comments", "").strip()
    feedback_received = request.form.get("feedback_received", "").strip()

    base_missing = not name or not email
    objective_missing = not objective_rating or not objective_comment
    abilities_missing = (
        not technical_rating
        or not project_rating
        or not methodology_rating
        or not abilities_comment
        or not efficiency_collaboration
        or not efficiency_ownership
        or not efficiency_resourcefulness
        or not efficiency_comment
        or not conduct_mutual_trust
        or not conduct_proactivity
        or not conduct_leadership
        or not conduct_comment
        or not general_comments
        or not feedback_received
    )
    objective_invalid = not _validate_choice(objective_rating, OBJECTIVE_CHOICES)
    abilities_invalid = not all(
        _validate_choice(val, ABILITY_CHOICES)
        for val in (
            technical_rating,
            project_rating,
            methodology_rating,
            efficiency_collaboration,
            efficiency_ownership,
            efficiency_resourcefulness,
            conduct_mutual_trust,
            conduct_proactivity,
            conduct_leadership,
        )
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
        Entry.query.filter(func.lower(Entry.name) == name.lower()).first() if name else None
    )
    if existing_entry:
        flash(
            "You already have a self assessment. Please edit your existing one instead.",
            "error",
        )
        return redirect(url_for("index"))

    entry = Entry(  # type: ignore[call-arg]
        name=name,
        email=email,
        manager_name=manager_name,
        objective_rating=objective_rating,
        objective_comment=objective_comment,
        technical_rating=technical_rating,
        project_rating=project_rating,
        methodology_rating=methodology_rating,
        abilities_comment=abilities_comment,
        efficiency_collaboration=efficiency_collaboration,
        efficiency_ownership=efficiency_ownership,
        efficiency_resourcefulness=efficiency_resourcefulness,
        efficiency_comment=efficiency_comment,
        conduct_mutual_trust=conduct_mutual_trust,
        conduct_proactivity=conduct_proactivity,
        conduct_leadership=conduct_leadership,
        conduct_comment=conduct_comment,
        general_comments=general_comments,
        feedback_received=feedback_received,
    )
    database.session.add(entry)
    database.session.commit()
    flash("Entry created", "success")
    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id: int) -> Union[str, Response]:
    """Edit an existing entry."""
    entry = Entry.query.get_or_404(entry_id)

    session_user = session.get("user", {})
    if not _can_access_entry(entry, session_user):
        flash("You are not allowed to access this entry", "error")
        return redirect(url_for("index"))

    # Check workflow status - only allow editing if created
    workflow_status = entry.workflow_status or STATUS_CREATED
    if workflow_status != STATUS_CREATED:
        if workflow_status == STATUS_FINALIZED:
            flash("Cannot edit this self-assessment because it has been finalized with manager.", "error")
        elif workflow_status == STATUS_SUBMITTED:
            flash("Cannot edit this self-assessment because it has been submitted to the program manager.", "error")
        elif workflow_status == STATUS_APPROVED:
            flash("Cannot edit this self-assessment because it has been approved by the program manager.", "error")
        else:
            flash("Cannot edit this self-assessment at this stage.", "error")
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
        abilities_comment = request.form.get("abilities_comment", "").strip()
        efficiency_collaboration = request.form.get("efficiency_collaboration", "").strip()
        efficiency_ownership = request.form.get("efficiency_ownership", "").strip()
        efficiency_resourcefulness = request.form.get("efficiency_resourcefulness", "").strip()
        efficiency_comment = request.form.get("efficiency_comment", "").strip()
        conduct_mutual_trust = request.form.get("conduct_mutual_trust", "").strip()
        conduct_proactivity = request.form.get("conduct_proactivity", "").strip()
        conduct_leadership = request.form.get("conduct_leadership", "").strip()
        conduct_comment = request.form.get("conduct_comment", "").strip()
        general_comments = request.form.get("general_comments", "").strip()
        feedback_received = request.form.get("feedback_received", "").strip()

        objective_missing = not objective_rating or not objective_comment
        abilities_missing = (
            not technical_rating
            or not project_rating
            or not methodology_rating
            or not abilities_comment
            or not efficiency_collaboration
            or not efficiency_ownership
            or not efficiency_resourcefulness
            or not efficiency_comment
            or not conduct_mutual_trust
            or not conduct_proactivity
            or not conduct_leadership
            or not conduct_comment
            or not general_comments
            or not feedback_received
        )
        objective_invalid = not _validate_choice(objective_rating, OBJECTIVE_CHOICES)
        abilities_invalid = not all(
            _validate_choice(val, ABILITY_CHOICES)
            for val in (
                technical_rating,
                project_rating,
                methodology_rating,
                efficiency_collaboration,
                efficiency_ownership,
                efficiency_resourcefulness,
                conduct_mutual_trust,
                conduct_proactivity,
                conduct_leadership,
            )
        )

        if objective_missing or abilities_missing or objective_invalid or abilities_invalid:
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
        entry.abilities_comment = abilities_comment
        entry.efficiency_collaboration = efficiency_collaboration
        entry.efficiency_ownership = efficiency_ownership
        entry.efficiency_resourcefulness = efficiency_resourcefulness
        entry.efficiency_comment = efficiency_comment
        entry.conduct_mutual_trust = conduct_mutual_trust
        entry.conduct_proactivity = conduct_proactivity
        entry.conduct_leadership = conduct_leadership
        entry.conduct_comment = conduct_comment
        entry.general_comments = general_comments
        entry.feedback_received = feedback_received
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
def delete_entry(entry_id: int) -> Response:
    """Delete an existing entry."""
    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})
    if not _can_access_entry(entry, session_user):
        flash("You are not allowed to access this entry", "error")
        return redirect(url_for("index"))

    # Check workflow status - only allow deleting if created
    workflow_status = entry.workflow_status or STATUS_CREATED
    if workflow_status != STATUS_CREATED:
        if workflow_status == STATUS_FINALIZED:
            flash("Cannot delete this self-assessment because it has been finalized with manager.", "error")
        elif workflow_status == STATUS_SUBMITTED:
            flash("Cannot delete this self-assessment because it has been submitted to the program manager.", "error")
        elif workflow_status == STATUS_APPROVED:
            flash("Cannot delete this self-assessment because it has been approved by the program manager.", "error")
        else:
            flash("Cannot delete this self-assessment at this stage.", "error")
        return redirect(url_for("index"))

    database.session.delete(entry)
    database.session.commit()
    flash("Entry deleted", "success")
    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/finalize", methods=["POST"])
@login_required
def finalize_entry(entry_id: int) -> Response:
    """Finalize an employee self assessment (manager creates final version)."""

    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})
    if not _can_manage_entry(entry, session_user):
        flash("Only the manager can finalize this entry.", "error")
        return redirect(url_for("index"))

    # Check if already finalized
    if entry.workflow_status and entry.workflow_status != STATUS_CREATED:
        flash("This entry has already been finalized.", "info")
        return redirect(url_for("edit_manager_entry", entry_id=entry.id))

    # Update workflow status and program manager
    entry.workflow_status = STATUS_FINALIZED
    entry.program_manager_name = session_user.get("program_manager_name") or ""
    database.session.commit()
    flash("Entry finalized. You can now edit manager comments.", "success")
    return redirect(url_for("edit_manager_entry", entry_id=entry.id))


@app.route("/entries/<int:entry_id>/edit_manager", methods=["GET", "POST"])
@login_required
def edit_manager_entry(entry_id: int) -> Union[str, Response]:
    """Edit manager comments for an entry (manager only)."""

    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})

    if not _can_manage_entry(entry, session_user):
        flash("You are not allowed to access this entry.", "error")
        return redirect(url_for("index"))

    if entry.workflow_status in (STATUS_SUBMITTED, STATUS_APPROVED):
        flash("This entry cannot be edited after submission to the program manager.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        # Editable manager fields
        manager_objective_comment = request.form.get("manager_objective_comment", "").strip()
        manager_abilities_comment = request.form.get("manager_abilities_comment", "").strip()
        manager_efficiency_comment = request.form.get("manager_efficiency_comment", "").strip()
        goals_2026 = request.form.get("goals_2026", "").strip()
        manager_general_comments = request.form.get("manager_general_comments", "").strip()

        # Validate only the editable manager fields
        manager_fields_missing = (
            not manager_objective_comment
            or not manager_abilities_comment
            or not manager_efficiency_comment
            or not goals_2026
            or not manager_general_comments
        )

        if manager_fields_missing:
            flash("All manager fields must be completed", "error")
            return redirect(url_for("edit_manager_entry", entry_id=entry_id))

        entry.manager_objective_comment = manager_objective_comment
        entry.manager_abilities_comment = manager_abilities_comment
        entry.manager_efficiency_comment = manager_efficiency_comment
        entry.goals_2026 = goals_2026
        entry.manager_general_comments = manager_general_comments
        database.session.commit()
        flash("Manager assessment updated", "success")
        return redirect(url_for("index"))

    return render_template(
        "final_edit.html",
        entry=entry,
        objective_choices=OBJECTIVE_CHOICES,
        ability_choices=ABILITY_CHOICES,
    )


@app.route("/entries/<int:entry_id>/submit", methods=["POST"])
@login_required
def submit_entry(entry_id: int) -> Response:
    """Submit a finalized entry to the program manager."""

    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})

    if not _can_manage_entry(entry, session_user):
        flash("You are not allowed to submit this entry.", "error")
        return redirect(url_for("index"))

    if entry.workflow_status != STATUS_FINALIZED:
        flash("Only finalized entries can be submitted to the program manager.", "error")
        return redirect(url_for("index"))

    entry.workflow_status = STATUS_SUBMITTED
    database.session.commit()
    flash("Entry submitted to program manager.", "success")
    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/approve", methods=["POST"])
@login_required
def approve_entry(entry_id: int) -> Response:
    """Approve a submitted entry as program manager."""

    entry = Entry.query.get_or_404(entry_id)
    session_user = session.get("user", {})

    if not _can_approve_entry(entry, session_user):
        flash("You are not allowed to approve this entry.", "error")
        return redirect(url_for("index"))

    if entry.workflow_status != STATUS_SUBMITTED:
        flash("Only submitted entries can be approved.", "error")
        return redirect(url_for("index"))

    entry.workflow_status = STATUS_APPROVED
    database.session.commit()
    flash("Entry approved by program manager.", "success")
    return redirect(url_for("index"))


@app.route("/login")
def login() -> Response:
    """Start Microsoft sign-in by redirecting to Azure AD."""

    next_path = request.args.get("next", "").strip()
    if next_path.startswith("/"):
        session["post_login_redirect"] = next_path

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
def authorized() -> Response:
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
        flash(f"Login failed: {result.get('error_description', 'Unknown error')}", "error")
        return redirect(url_for("index"))

    claims = result.get("id_token_claims", {})
    access_token = result.get("access_token", "")
    manager_name, program_manager_name = _fetch_manager_hierarchy(access_token or "")
    direct_reports = _fetch_direct_reports(access_token or "")
    user_name = claims.get("name")
    user_email = claims.get("preferred_username")

    app.logger.info(
        "[AUTH_AUDIT] Resolved manager hierarchy for login user oid=%s email=%s manager=%s program_manager=%s",
        claims.get("oid") or "",
        user_email or "",
        manager_name or "",
        program_manager_name or "",
    )

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
        "program_manager_name": program_manager_name,
        "direct_reports": direct_reports,
        "direct_reports_refreshed_at": _utc_now().isoformat(),
    }
    flash("Signed in with Microsoft 365", "success")
    post_login_redirect = session.pop("post_login_redirect", "")
    if isinstance(post_login_redirect, str) and post_login_redirect.startswith("/"):
        return redirect(post_login_redirect)
    return redirect(url_for("index"))


@app.route("/logout")
def logout() -> Response:
    """Clear local session and sign out of Azure AD."""

    session.clear()
    post_logout = url_for("index", _external=True)
    return redirect(f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={post_logout}")


if __name__ == "__main__":
    app.run(debug=True)
