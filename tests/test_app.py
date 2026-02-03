"""Unit tests for the Employee Dialogue app."""

import pytest

from employee_dialogue import ABILITY_CHOICES
from employee_dialogue import OBJECTIVE_CHOICES
from employee_dialogue import Entry
from employee_dialogue import FinalEntry
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

    def test_final_entry_creation(self, client):
        """Test creating a FinalEntry."""
        with app.app_context():
            final = FinalEntry(
                source_entry_id=1,
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
            database.session.add(final)
            database.session.commit()

            assert final.id is not None
            assert final.source_entry_id == 1


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
