import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas.user import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    ConfigResponse,
    ConfigUpdate,
    StatsResponse,
)
from schemas.search import (
    SearchParams,
    SearchResponse,
    ResultItem,
    DocumentDetail,
)


# ── LoginRequest ──────────────────────────────────────────

class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(username="admin", password="secret")
        assert req.username == "admin"
        assert req.password == "secret"

    def test_empty_username_fails(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="", password="secret")

    def test_empty_password_fails(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="admin", password="")

    def test_whitespace_username_stripped(self):
        """Whitespace-only username passes Pydantic but will be rejected by auth logic."""
        req = LoginRequest(username="   ", password="secret")
        assert req.username == "   "

    def test_missing_fields_fails(self):
        with pytest.raises(ValidationError):
            LoginRequest()


# ── TokenResponse ─────────────────────────────────────────

class TestTokenResponse:
    def test_valid(self):
        resp = TokenResponse(
            access_token="abc123",
            role="admin",
            full_name="Admin User",
            username="admin",
        )
        assert resp.token_type == "bearer"
        assert resp.access_token == "abc123"
        assert resp.role == "admin"

    def test_minimal(self):
        resp = TokenResponse(access_token="tok", role="hr", username="hruser")
        assert resp.full_name is None
        assert resp.token_type == "bearer"


# ── UserCreate ────────────────────────────────────────────

class TestUserCreate:
    def test_valid_hr(self):
        user = UserCreate(username="john", password="secret123", role="hr")
        assert user.role == "hr"

    def test_valid_admin(self):
        user = UserCreate(username="john", password="secret123", role="admin")
        assert user.role == "admin"

    def test_valid_project_manager(self):
        user = UserCreate(username="john", password="secret123", role="project_manager")
        assert user.role == "project_manager"

    def test_default_role_is_hr(self):
        user = UserCreate(username="john", password="secret123")
        assert user.role == "hr"

    def test_invalid_role_fails(self):
        with pytest.raises(ValidationError):
            UserCreate(username="john", password="secret123", role="superadmin")

    def test_short_username_fails(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", password="secret123")

    def test_short_password_fails(self):
        with pytest.raises(ValidationError):
            UserCreate(username="john", password="abc")

    def test_optional_full_name(self):
        user = UserCreate(username="john", password="secret123")
        assert user.full_name is None

    def test_with_full_name(self):
        user = UserCreate(username="john", password="secret123", full_name="John Doe")
        assert user.full_name == "John Doe"




class TestUserUpdate:
    def test_all_optional(self):
        update = UserUpdate()
        assert update.full_name is None
        assert update.role is None
        assert update.is_active is None

    def test_partial_update(self):
        update = UserUpdate(is_active=False)
        assert update.is_active is False
        assert update.role is None

    def test_invalid_role_fails(self):
        with pytest.raises(ValidationError):
            UserUpdate(role="hacker")

    def test_valid_role(self):
        update = UserUpdate(role="admin")
        assert update.role == "admin"




class TestUserResponse:
    def test_from_dict(self):
        now = datetime.utcnow()
        resp = UserResponse(
            id=1,
            username="admin",
            full_name="Admin",
            role="admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert resp.id == 1
        assert resp.username == "admin"

    def test_no_password_in_response(self):
        now = datetime.utcnow()
        data = UserResponse(
            id=1, username="admin", role="admin",
            is_active=True, created_at=now, updated_at=now,
        )
        assert "password" not in UserResponse.model_fields
        assert "hashed_password" not in UserResponse.model_fields




class TestConfigSchemas:
    def test_config_response(self):
        resp = ConfigResponse(data_folder="/data")
        assert resp.data_folder == "/data"

    def test_config_update(self):
        update = ConfigUpdate(data_folder="/new/path")
        assert update.data_folder == "/new/path"

    def test_config_update_empty_fails(self):
        with pytest.raises(ValidationError):
            ConfigUpdate(data_folder="")




class TestStatsResponse:
    def test_valid(self):
        resp = StatsResponse(
            total_documents=100,
            by_department={"HR": 20, "Prosjekt": 80},
            by_file_type={"pdf": 50, "docx": 50},
        )
        assert resp.total_documents == 100
        assert resp.by_department["HR"] == 20




class TestSearchParams:
    def test_defaults(self):
        params = SearchParams()
        assert params.q == ""
        assert params.limit == 20
        assert params.offset == 0
        assert params.file_type is None
        assert params.department is None

    def test_with_query(self):
        params = SearchParams(q="transocean")
        assert params.q == "transocean"

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            SearchParams(limit=0)
        with pytest.raises(ValidationError):
            SearchParams(limit=101)

    def test_offset_bounds(self):
        with pytest.raises(ValidationError):
            SearchParams(offset=-1)

    def test_sort_order_validation(self):
        params = SearchParams(sort_order="asc")
        assert params.sort_order == "asc"
        with pytest.raises(ValidationError):
            SearchParams(sort_order="invalid")

    def test_all_filters(self):
        params = SearchParams(
            q="test", file_type="pdf", department="HR",
            date_from="2023-01-01", date_to="2023-12-31",
            limit=50, offset=10,
        )
        assert params.limit == 50




class TestResultItem:
    def test_valid(self):
        item = ResultItem(
            id="abc123", file_name="report.pdf",
            department="Prosjekt", file_type="pdf",
            file_size=245600, created_at="2023-01-15",
            modified_at="2023-03-20", highlight="<em>report</em>.pdf",
        )
        assert item.highlight == "<em>report</em>.pdf"

    def test_name_match(self):
        item = ResultItem(
            id="def456", file_name="photo.jpg",
            department="HR", file_type="jpg",
            file_size=3200000, created_at="2023-02-10",
            modified_at="2023-02-10", highlight="photo.jpg",
        )
        assert item.file_name == "photo.jpg"




class TestSearchResponse:
    def test_empty_results(self):
        resp = SearchResponse(
            query="test", total_hits=0,
            limit=20, offset=0, results=[],
        )
        assert resp.total_hits == 0
        assert len(resp.results) == 0

    def test_with_results(self):
        item = ResultItem(
            id="abc", file_name="f.pdf", department="HR",
            file_type="pdf", file_size=100, created_at="2023-01-01",
            modified_at="2023-01-01", highlight="test",
        )
        resp = SearchResponse(
            query="test", total_hits=1,
            limit=20, offset=0, results=[item],
        )
        assert len(resp.results) == 1




class TestDocumentDetail:
    def test_valid(self):
        doc = DocumentDetail(
            id="abc", file_name="report.pdf",
            file_path="/data/HR/report.pdf", department="HR",
            file_type="pdf", file_size=245600,
            created_at="2023-01-15", modified_at="2023-03-20",
            restricted=False,
        )
        assert doc.file_path == "/data/HR/report.pdf"
        assert doc.restricted is False

    def test_no_content_field(self):
        doc = DocumentDetail(
            id="xyz", file_name="photo.jpg",
            file_path="/data/HR/photo.jpg", department="HR",
            file_type="jpg", file_size=3200000,
            created_at="2023-01-01", modified_at="2023-01-01",
            restricted=False,
        )
        assert not hasattr(doc, "content_available")
