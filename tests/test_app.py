"""Unit tests for the Employee Dialogue app."""

import pytest

import employee_dialogue as app_module

from employee_dialogue import ABILITY_CHOICES
from employee_dialogue import COMMENT_MAX_LENGTH
from employee_dialogue import OBJECTIVE_CHOICES
from employee_dialogue import STATUS_APPROVED
from employee_dialogue import STATUS_CREATED
from employee_dialogue import STATUS_FINALIZED
from employee_dialogue import STATUS_SUBMITTED
from employee_dialogue import Entry
from employee_dialogue import _can_access_entry
from employee_dialogue import _can_manage_entry
from employee_dialogue import _validate_choice
from employee_dialogue import app
from employee_dialogue import database


@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test-secret-key"

    with app.test_client() as client:
        with app.app_context():
            database.create_all()
        yield client
        with app.app_context():
            database.drop_all()


@pytest.fixture
def authenticated_session(client):
    """Create an authenticated session."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "name": "Test User",
            "email": "test@example.com",
            "oid": "test-oid",
            "manager_name": "Test Manager",
        }
    return client


class TestModels:
    """Test database models."""

    def test_entry_creation(self, client):
        """Test creating an Entry."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="Test Manager",
                objective_rating="Achieved objective",
                objective_comment="Test comment",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test abilities",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test efficiency",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test conduct",
                general_comments="Test general",
            )
            database.session.add(entry)
            database.session.commit()

            assert entry.id is not None
            assert entry.name == "Test User"
            assert entry.created_at is not None
            assert entry.updated_at is not None

    def test_entry_with_workflow_status(self, client):
        """Test Entry with workflow status and manager fields."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="Test Manager",
                objective_rating="Achieved objective",
                objective_comment="Test comment",
                manager_objective_comment="Manager comment",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test abilities",
                manager_abilities_comment="Manager abilities comment",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test efficiency",
                manager_efficiency_comment="Manager efficiency comment",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test conduct",
                general_comments="Test general",
                goals_2026="Test goals",
                manager_general_comments="Manager general comments",
                feedback_received="Yes",
                program_manager_name="Program Manager",
                workflow_status=STATUS_FINALIZED,
            )
            database.session.add(entry)
            database.session.commit()

            assert entry.id is not None
            assert entry.workflow_status == STATUS_FINALIZED
            assert entry.manager_objective_comment == "Manager comment"
            assert entry.program_manager_name == "Program Manager"


class TestValidation:
    """Test validation functions."""

    def test_validate_choice_valid(self):
        """Test _validate_choice with valid input."""
        assert _validate_choice("Achieved objective", OBJECTIVE_CHOICES) is True
        assert _validate_choice("Meets expectations", ABILITY_CHOICES) is True

    def test_validate_choice_invalid(self):
        """Test _validate_choice with invalid input."""
        assert _validate_choice("Invalid choice", OBJECTIVE_CHOICES) is False
        assert _validate_choice("", ABILITY_CHOICES) is False

    def test_can_access_entry(self, client):
        """Test _can_access_entry permission check."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
            )

            session_user = {"name": "Test User"}
            assert _can_access_entry(entry, session_user) is True

            other_user = {"name": "Other User"}
            assert _can_access_entry(entry, other_user) is False

    def test_can_manage_entry(self, client):
        """Test _can_manage_entry permission check."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="Manager Name",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
            )

            manager = {"name": "Manager Name"}
            assert _can_manage_entry(entry, manager) is True

            non_manager = {"name": "Other User"}
            assert _can_manage_entry(entry, non_manager) is False


class TestRoutes:
    """Test Flask routes."""

    def test_index_redirect_without_auth(self, client):
        """Test index redirects to login when not authenticated."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_index_with_auth(self, authenticated_session):
        """Test index loads when authenticated."""
        response = authenticated_session.get("/")
        assert response.status_code == 200
        assert b"Your Self Assessment" in response.data

    def test_new_entry_redirect_without_auth(self, client):
        """Test new entry redirects to login when not authenticated."""
        response = client.get("/entries/new")
        assert response.status_code == 302

    def test_new_entry_with_auth(self, authenticated_session):
        """Test new entry form loads when authenticated."""
        response = authenticated_session.get("/entries/new")
        assert response.status_code == 200
        assert b"New Self Assessment" in response.data

    def test_create_entry_validation(self, authenticated_session):
        """Test create entry with missing fields."""
        response = authenticated_session.post(
            "/entries",
            data={
                "objective_rating": "Achieved objective",
                # Missing other required fields
            },
        )
        assert response.status_code == 302
        # Should redirect back with error

    def test_create_entry_success(self, authenticated_session):
        """Test successful entry creation."""
        with app.app_context():
            response = authenticated_session.post(
                "/entries",
                data={
                    "objective_rating": "Achieved objective",
                    "objective_comment": "Test objective comment",
                    "technical_rating": "Meets expectations",
                    "project_rating": "Meets expectations",
                    "methodology_rating": "Meets expectations",
                    "abilities_comment": "Test abilities comment",
                    "efficiency_collaboration": "Meets expectations",
                    "efficiency_ownership": "Meets expectations",
                    "efficiency_resourcefulness": "Meets expectations",
                    "efficiency_comment": "Test efficiency comment",
                    "conduct_mutual_trust": "Meets expectations",
                    "conduct_proactivity": "Meets expectations",
                    "conduct_leadership": "N/A",
                    "conduct_comment": "Test conduct comment",
                    "general_comments": "Test general comments",
                    "feedback_received": "Yes",
                },
            )
            assert response.status_code == 302

            # Verify entry was created
            entry = Entry.query.first()
            assert entry is not None
            assert entry.name == "Test User"
            assert entry.objective_rating == "Achieved objective"

    def test_delete_entry(self, authenticated_session):
        """Test deleting an entry."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        response = authenticated_session.post(f"/entries/{entry_id}/delete")
        assert response.status_code == 302

        with app.app_context():
            deleted_entry = database.session.get(Entry, entry_id)
            assert deleted_entry is None

    def test_delete_finalized_entry_allowed_for_testing(self, authenticated_session):
        """Test temporary testing override allows deleting finalized entries."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="Test Manager",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_FINALIZED,
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        response = authenticated_session.post(f"/entries/{entry_id}/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"Testing mode: deleting a self-assessment in any workflow status is temporarily enabled." in response.data

        with app.app_context():
            deleted_entry = database.session.get(Entry, entry_id)
            assert deleted_entry is None

    def test_delete_submitted_entry_allowed_for_testing(self, authenticated_session):
        """Test temporary testing override allows deleting submitted entries."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="Test Manager",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_SUBMITTED,
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        response = authenticated_session.post(f"/entries/{entry_id}/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"Testing mode: deleting a self-assessment in any workflow status is temporarily enabled." in response.data

        with app.app_context():
            deleted_entry = database.session.get(Entry, entry_id)
            assert deleted_entry is None

    def test_delete_approved_entry_allowed_for_testing(self, authenticated_session):
        """Test temporary testing override allows deleting approved entries."""
        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="Test Manager",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_APPROVED,
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        response = authenticated_session.post(f"/entries/{entry_id}/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"Testing mode: deleting a self-assessment in any workflow status is temporarily enabled." in response.data

        with app.app_context():
            deleted_entry = database.session.get(Entry, entry_id)
            assert deleted_entry is None

    def test_login_route(self, client):
        """Test login route redirects to Microsoft."""
        response = client.get("/login")
        assert response.status_code == 302
        assert "login.microsoftonline.com" in response.location

    def test_logout_route(self, authenticated_session):
        """Test logout clears session."""
        response = authenticated_session.get("/logout")
        assert response.status_code == 302
        assert "logout" in response.location


class TestFormValidation:
    """Test form field validation."""

    def test_create_rejects_comment_longer_than_limit(self, authenticated_session):
        """Test create rejects comments longer than COMMENT_MAX_LENGTH."""

        too_long_comment = "x" * (COMMENT_MAX_LENGTH + 1)
        response = authenticated_session.post(
            "/entries",
            data={
                "objective_rating": "Achieved objective",
                "objective_comment": too_long_comment,
                "technical_rating": "Meets expectations",
                "project_rating": "Meets expectations",
                "methodology_rating": "Meets expectations",
                "abilities_comment": "Test",
                "efficiency_collaboration": "Meets expectations",
                "efficiency_ownership": "Meets expectations",
                "efficiency_resourcefulness": "Meets expectations",
                "efficiency_comment": "Test",
                "conduct_mutual_trust": "Meets expectations",
                "conduct_proactivity": "Meets expectations",
                "conduct_leadership": "N/A",
                "conduct_comment": "Test",
                "general_comments": "Test",
                "feedback_received": "Yes",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Comment fields must be 1000 characters or fewer" in response.data
        with app.app_context():
            assert Entry.query.count() == 0

    def test_edit_rejects_comment_longer_than_limit(self, authenticated_session):
        """Test edit rejects comments longer than COMMENT_MAX_LENGTH."""

        with app.app_context():
            entry = Entry(
                name="Test User",
                email="test@example.com",
                manager_name="",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Original general comments",
                feedback_received="Yes",
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        too_long_comment = "x" * (COMMENT_MAX_LENGTH + 1)
        response = authenticated_session.post(
            f"/entries/{entry_id}/edit",
            data={
                "objective_rating": "Achieved objective",
                "objective_comment": "Test",
                "technical_rating": "Meets expectations",
                "project_rating": "Meets expectations",
                "methodology_rating": "Meets expectations",
                "abilities_comment": "Test",
                "efficiency_collaboration": "Meets expectations",
                "efficiency_ownership": "Meets expectations",
                "efficiency_resourcefulness": "Meets expectations",
                "efficiency_comment": "Test",
                "conduct_mutual_trust": "Meets expectations",
                "conduct_proactivity": "Meets expectations",
                "conduct_leadership": "N/A",
                "conduct_comment": "Test",
                "general_comments": too_long_comment,
                "feedback_received": "Yes",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Comment fields must be 1000 characters or fewer" in response.data

        with app.app_context():
            persisted_entry = database.session.get(Entry, entry_id)
            assert persisted_entry is not None
            assert persisted_entry.general_comments == "Original general comments"

    def test_invalid_objective_rating(self, authenticated_session):
        """Test rejection of invalid objective rating."""
        response = authenticated_session.post(
            "/entries",
            data={
                "objective_rating": "Invalid Rating",
                "objective_comment": "Test",
                "technical_rating": "Meets expectations",
                "project_rating": "Meets expectations",
                "methodology_rating": "Meets expectations",
                "abilities_comment": "Test",
                "efficiency_collaboration": "Meets expectations",
                "efficiency_ownership": "Meets expectations",
                "efficiency_resourcefulness": "Meets expectations",
                "efficiency_comment": "Test",
                "conduct_mutual_trust": "Meets expectations",
                "conduct_proactivity": "Meets expectations",
                "conduct_leadership": "N/A",
                "conduct_comment": "Test",
                "general_comments": "Test",
            },
        )
        assert response.status_code == 302


class TestSecurityControls:
    """Security-focused route authorization and workflow tampering tests."""

    def test_submit_denied_for_non_manager(self, client):
        """Direct submit POST should be blocked when requester is not the manager."""

        with app.app_context():
            entry = Entry(
                name="Employee User",
                email="employee@example.com",
                manager_name="Manager User",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_FINALIZED,
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Other User",
                "email": "other@example.com",
                "oid": "other-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        response = client.post(f"/entries/{entry_id}/submit", follow_redirects=True)
        assert response.status_code == 200
        assert b"You are not allowed to submit this entry." in response.data

        with app.app_context():
            persisted_entry = database.session.get(Entry, entry_id)
            assert persisted_entry is not None
            assert persisted_entry.workflow_status == STATUS_FINALIZED

    def test_submit_blocked_when_entry_not_finalized(self, client):
        """Direct submit POST should not bypass required finalized state."""

        with app.app_context():
            entry = Entry(
                name="Employee User",
                email="employee@example.com",
                manager_name="Manager User",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_CREATED,
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Manager User",
                "email": "manager@example.com",
                "oid": "manager-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        response = client.post(f"/entries/{entry_id}/submit", follow_redirects=True)
        assert response.status_code == 200
        assert b"Only finalized entries can be submitted to the program manager." in response.data

        with app.app_context():
            persisted_entry = database.session.get(Entry, entry_id)
            assert persisted_entry is not None
            assert persisted_entry.workflow_status == STATUS_CREATED

    def test_approve_denied_for_non_program_manager(self, client):
        """Direct approve POST should be blocked when requester is not designated PM."""

        with app.app_context():
            entry = Entry(
                name="Employee User",
                email="employee@example.com",
                manager_name="Manager User",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_SUBMITTED,
                program_manager_name="Program Manager",
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Not Program Manager",
                "email": "other@example.com",
                "oid": "other-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        response = client.post(f"/entries/{entry_id}/approve", follow_redirects=True)
        assert response.status_code == 200
        assert b"You are not allowed to approve this entry." in response.data

        with app.app_context():
            persisted_entry = database.session.get(Entry, entry_id)
            assert persisted_entry is not None
            assert persisted_entry.workflow_status == STATUS_SUBMITTED

    def test_approve_blocked_when_entry_not_submitted(self, client):
        """Direct approve POST should not bypass required submitted state."""

        with app.app_context():
            entry = Entry(
                name="Employee User",
                email="employee@example.com",
                manager_name="Manager User",
                objective_rating="Achieved objective",
                objective_comment="Test",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Test",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Test",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Test",
                general_comments="Test",
                workflow_status=STATUS_FINALIZED,
                program_manager_name="Program Manager",
            )
            database.session.add(entry)
            database.session.commit()
            entry_id = entry.id

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Program Manager",
                "email": "pm@example.com",
                "oid": "pm-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        response = client.post(f"/entries/{entry_id}/approve", follow_redirects=True)
        assert response.status_code == 200
        assert b"Only submitted entries can be approved." in response.data

        with app.app_context():
            persisted_entry = database.session.get(Entry, entry_id)
            assert persisted_entry is not None
            assert persisted_entry.workflow_status == STATUS_FINALIZED

    def test_invalid_ability_rating(self, authenticated_session):
        """Test rejection of invalid ability rating."""
        response = authenticated_session.post(
            "/entries",
            data={
                "objective_rating": "Achieved objective",
                "objective_comment": "Test",
                "technical_rating": "Invalid Rating",
                "project_rating": "Meets expectations",
                "methodology_rating": "Meets expectations",
                "abilities_comment": "Test",
                "efficiency_collaboration": "Meets expectations",
                "efficiency_ownership": "Meets expectations",
                "efficiency_resourcefulness": "Meets expectations",
                "efficiency_comment": "Test",
                "conduct_mutual_trust": "Meets expectations",
                "conduct_proactivity": "Meets expectations",
                "conduct_leadership": "N/A",
                "conduct_comment": "Test",
                "general_comments": "Test",
            },
        )
        assert response.status_code == 302


class TestSubmissionEmail:
    """Test submission email behavior."""

    def test_manager_edit_rejects_comment_longer_than_limit(self, client):
        """Test manager finalize form rejects comments longer than COMMENT_MAX_LENGTH."""

        entry_id = self._create_created_entry()

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Manager User",
                "email": "manager@example.com",
                "oid": "manager-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        too_long_comment = "x" * (COMMENT_MAX_LENGTH + 1)
        response = client.post(
            f"/entries/{entry_id}/edit_manager",
            data={
                "manager_objective_comment": "Updated manager objective",
                "manager_abilities_comment": "Updated manager abilities",
                "manager_efficiency_comment": "Updated manager efficiency",
                "goals_2026": "Updated goals",
                "manager_general_comments": too_long_comment,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Comment fields must be 1000 characters or fewer" in response.data

        with app.app_context():
            unchanged_entry = database.session.get(Entry, entry_id)
            assert unchanged_entry is not None
            assert unchanged_entry.workflow_status == STATUS_CREATED
            assert unchanged_entry.manager_general_comments == "Manager general"

    def test_manager_edit_rejects_goals_longer_than_limit(self, client):
        """Test manager finalize form rejects goals longer than COMMENT_MAX_LENGTH."""

        entry_id = self._create_created_entry()

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Manager User",
                "email": "manager@example.com",
                "oid": "manager-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        too_long_goals = "x" * (COMMENT_MAX_LENGTH + 1)
        response = client.post(
            f"/entries/{entry_id}/edit_manager",
            data={
                "manager_objective_comment": "Updated manager objective",
                "manager_abilities_comment": "Updated manager abilities",
                "manager_efficiency_comment": "Updated manager efficiency",
                "goals_2026": too_long_goals,
                "manager_general_comments": "Updated manager general",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Comment fields must be 1000 characters or fewer" in response.data

        with app.app_context():
            unchanged_entry = database.session.get(Entry, entry_id)
            assert unchanged_entry is not None
            assert unchanged_entry.workflow_status == STATUS_CREATED
            assert unchanged_entry.goals_2026 == "Goals"

    def test_assessment_email_body_preserves_multiline_comments(self):
        """Test summary email keeps user-entered line breaks in multiline fields."""

        entry = Entry(
            name="Employee User",
            email="employee@example.com",
            manager_name="Manager User",
            objective_rating="Achieved objective",
            objective_comment="Line one\r\nLine two",
            manager_objective_comment="Mgr one\nMgr two",
            technical_rating="Meets expectations",
            project_rating="Meets expectations",
            methodology_rating="Meets expectations",
            abilities_comment="A1\nA2",
            manager_abilities_comment="MA1",
            efficiency_collaboration="Meets expectations",
            efficiency_ownership="Meets expectations",
            efficiency_resourcefulness="Meets expectations",
            efficiency_comment="E1\nE2",
            manager_efficiency_comment="ME1",
            conduct_mutual_trust="Meets expectations",
            conduct_proactivity="Meets expectations",
            conduct_leadership="N/A",
            conduct_comment="C1\nC2",
            general_comments="G1\nG2",
            goals_2026="Goal1\nGoal2",
            manager_general_comments="MG1\nMG2",
            feedback_received="Yes",
            workflow_status=STATUS_FINALIZED,
        )

        body = app_module._assessment_email_body(entry)

        assert "- Employee Comment:\n  Line one\n  Line two" in body
        assert "- Manager Comment:\n  Mgr one\n  Mgr two" in body
        assert "- Employee General Comments:\n  G1\n  G2" in body
        assert "- Goals 2026:\n  Goal1\n  Goal2" in body

    def _create_created_entry(self) -> int:
        with app.app_context():
            entry = Entry(
                name="Employee User",
                email="employee@example.com",
                manager_name="Manager User",
                objective_rating="Achieved objective",
                objective_comment="Objective comment",
                manager_objective_comment="Manager objective",
                technical_rating="Meets expectations",
                project_rating="Meets expectations",
                methodology_rating="Meets expectations",
                abilities_comment="Abilities comment",
                manager_abilities_comment="Manager abilities",
                efficiency_collaboration="Meets expectations",
                efficiency_ownership="Meets expectations",
                efficiency_resourcefulness="Meets expectations",
                efficiency_comment="Efficiency comment",
                manager_efficiency_comment="Manager efficiency",
                conduct_mutual_trust="Meets expectations",
                conduct_proactivity="Meets expectations",
                conduct_leadership="N/A",
                conduct_comment="Conduct comment",
                general_comments="General comments",
                goals_2026="Goals",
                manager_general_comments="Manager general",
                feedback_received="Yes",
            )
            database.session.add(entry)
            database.session.commit()
            return entry.id

    def test_save_final_assessment_sends_authenticated_summary_email(self, client, monkeypatch):
        """Test manager save final assessment sends summary email using SMTP authentication."""

        entry_id = self._create_created_entry()

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Manager User",
                "email": "manager@example.com",
                "oid": "manager-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        sent: dict[str, object] = {}

        class DummySMTP:
            def __init__(self, host, port, timeout):
                sent["host"] = host
                sent["port"] = port
                sent["timeout"] = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def login(self, username, password):
                sent["username"] = username
                sent["password"] = password

            def send_message(self, message):
                sent["to"] = message["To"]
                sent["subject"] = message["Subject"]

        monkeypatch.setattr(app_module.smtplib, "SMTP", DummySMTP)
        monkeypatch.setattr(app_module, "SMTP_HOST", "localhost")
        monkeypatch.setattr(app_module, "SMTP_PORT", 1587)
        monkeypatch.setattr(app_module, "SMTP_USERNAME", "xxx@euro-fusion.org")
        monkeypatch.setattr(app_module, "SMTP_PASSWORD", "yyy")

        response = client.post(
            f"/entries/{entry_id}/edit_manager",
            data={
                "manager_objective_comment": "Updated manager objective",
                "manager_abilities_comment": "Updated manager abilities",
                "manager_efficiency_comment": "Updated manager efficiency",
                "goals_2026": "Updated goals",
                "manager_general_comments": "Updated manager general",
            },
        )
        assert response.status_code == 302

        with app.app_context():
            finalized_entry = database.session.get(Entry, entry_id)
            assert finalized_entry is not None
            assert finalized_entry.workflow_status == STATUS_FINALIZED

        assert sent["host"] == "localhost"
        assert sent["port"] == 1587
        assert sent["username"] == "xxx@euro-fusion.org"
        assert sent["password"] == "yyy"
        recipients = {part.strip() for part in str(sent["to"]).split(",")}
        assert recipients == {"employee@example.com", "manager@example.com"}
        assert "Assessment finalized" in str(sent["subject"])

    def test_save_final_assessment_keeps_finalize_when_email_fails(self, client, monkeypatch):
        """Test manager save still finalizes entry when SMTP send fails."""

        entry_id = self._create_created_entry()

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Manager User",
                "email": "manager@example.com",
                "oid": "manager-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        class FailingSMTP:
            def __init__(self, host, port, timeout):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def login(self, username, password):
                raise RuntimeError("SMTP unavailable")

            def send_message(self, message):
                return None

        monkeypatch.setattr(app_module.smtplib, "SMTP", FailingSMTP)
        monkeypatch.setattr(app_module, "SMTP_HOST", "localhost")
        monkeypatch.setattr(app_module, "SMTP_PORT", 1587)
        monkeypatch.setattr(app_module, "SMTP_USERNAME", "xxx@euro-fusion.org")
        monkeypatch.setattr(app_module, "SMTP_PASSWORD", "yyy")

        response = client.post(
            f"/entries/{entry_id}/edit_manager",
            data={
                "manager_objective_comment": "Updated manager objective",
                "manager_abilities_comment": "Updated manager abilities",
                "manager_efficiency_comment": "Updated manager efficiency",
                "goals_2026": "Updated goals",
                "manager_general_comments": "Updated manager general",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"summary email could not be sent" in response.data

        with app.app_context():
            finalized_entry = database.session.get(Entry, entry_id)
            assert finalized_entry is not None
            assert finalized_entry.workflow_status == STATUS_FINALIZED

    def test_submit_entry_does_not_depend_on_email_delivery(self, client, monkeypatch):
        """Test submit route updates workflow without attempting SMTP delivery."""

        entry_id = self._create_created_entry()

        with app.app_context():
            entry = database.session.get(Entry, entry_id)
            assert entry is not None
            entry.workflow_status = STATUS_FINALIZED
            database.session.commit()

        with client.session_transaction() as sess:
            sess["user"] = {
                "name": "Manager User",
                "email": "manager@example.com",
                "oid": "manager-oid",
                "manager_name": "Program Manager",
                "program_manager_name": "Program Manager",
            }

        class FailIfConstructedSMTP:
            def __init__(self, host, port, timeout):
                raise AssertionError("SMTP should not be used by submit route")

        monkeypatch.setattr(app_module.smtplib, "SMTP", FailIfConstructedSMTP)

        response = client.post(f"/entries/{entry_id}/submit")
        assert response.status_code == 302

        with app.app_context():
            submitted_entry = database.session.get(Entry, entry_id)
            assert submitted_entry is not None
            assert submitted_entry.workflow_status == STATUS_SUBMITTED
