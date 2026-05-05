import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from services.auth import create_token
from services.meili_service import setup_index, add_document, delete_index


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a TestClient for document endpoint testing."""
    from main import app
    from database import engine, Base
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def clean_index():
    """Provide a clean Meilisearch index."""
    delete_index()
    setup_index()
    yield
    delete_index()
    setup_index()


@pytest.fixture
def sample_docs(clean_index):
    """Add sample documents pointing to real test fixture files."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    docs = [
        {
            "id": "doc001",
            "file_name": "sample.pdf",
            "file_path": str(fixtures_dir / "sample.pdf"),
            "department": "Prosjekt",
            "file_type": "pdf",
            "file_size": 1000,
            "created_at": "2023-01-15",
            "modified_at": "2023-03-20",
            "restricted": False,
        },
        {
            "id": "doc002",
            "file_name": "sample.docx",
            "file_path": str(fixtures_dir / "sample.docx"),
            "department": "HR",
            "file_type": "docx",
            "file_size": 2000,
            "created_at": "2023-02-01",
            "modified_at": "2023-04-10",
            "restricted": False,
        },
        {
            "id": "doc003",
            "file_name": "sample.xlsx",
            "file_path": str(fixtures_dir / "sample.xlsx"),
            "department": "Driftsmøter",
            "file_type": "xlsx",
            "file_size": 3000,
            "created_at": "2023-03-01",
            "modified_at": "2023-03-01",
            "restricted": False,
        },
        {
            "id": "doc_ghost",
            "file_name": "ghost.txt",
            "file_path": "/nonexistent/path/ghost.txt",
            "department": "Prosjekt",
            "file_type": "txt",
            "file_size": 0,
            "created_at": "2023-01-01",
            "modified_at": "2023-01-01",
            "restricted": False,
        },
    ]
    for doc in docs:
        add_document(doc)
    return docs


@pytest.fixture
def admin_token(admin_user):
    return create_token({"sub": admin_user.username, "role": admin_user.role, "full_name": ""})


@pytest.fixture
def hr_token(hr_user):
    return create_token({"sub": hr_user.username, "role": hr_user.role, "full_name": ""})


@pytest.fixture
def pm_token(pm_user):
    return create_token({"sub": pm_user.username, "role": pm_user.role, "full_name": ""})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── GET /api/docs/{id} — metadata ────────────────────────

class TestGetMetadata:
    def test_get_doc_metadata(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc001", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "doc001"
        assert data["file_name"] == "sample.pdf"
        assert data["department"] == "Prosjekt"
        assert data["file_type"] == "pdf"

    def test_get_doc_not_found(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/nonexistent123", headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_get_doc_requires_auth(self, client, sample_docs):
        resp = client.get("/api/docs/doc001")
        assert resp.status_code == 401

    def test_get_doc_metadata_fields(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc001", headers=auth_header(admin_token))
        data = resp.json()
        for field in ["id", "file_name", "file_path", "department", "file_type",
                       "file_size", "created_at", "modified_at", "restricted"]:
            assert field in data




class TestPreview:
    def test_preview_pdf(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc001/preview", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/pdf")

    def test_preview_docx(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc002/preview", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "wordprocessingml" in resp.headers["content-type"]

    def test_preview_file_not_on_disk(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc_ghost/preview", headers=auth_header(admin_token))
        assert resp.status_code == 404
        assert "disk" in resp.json()["detail"].lower()

    def test_preview_requires_auth(self, client, sample_docs):
        resp = client.get("/api/docs/doc001/preview")
        assert resp.status_code == 401




class TestDownload:
    def test_download_file(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc001/download", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/octet-stream"
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_download_file_not_on_disk(self, client, sample_docs, admin_token):
        resp = client.get("/api/docs/doc_ghost/download", headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_download_requires_auth(self, client, sample_docs):
        resp = client.get("/api/docs/doc001/download")
        assert resp.status_code == 401




class TestDocRoleAccess:
    def test_hr_cannot_access_prosjekt(self, client, sample_docs, hr_token):
        resp = client.get("/api/docs/doc001", headers=auth_header(hr_token))
        assert resp.status_code == 403

    def test_hr_can_access_hr(self, client, sample_docs, hr_token):
        resp = client.get("/api/docs/doc002", headers=auth_header(hr_token))
        assert resp.status_code == 200

    def test_hr_can_access_driftsmoter(self, client, sample_docs, hr_token):
        resp = client.get("/api/docs/doc003", headers=auth_header(hr_token))
        assert resp.status_code == 200

    def test_pm_cannot_access_hr(self, client, sample_docs, pm_token):
        resp = client.get("/api/docs/doc002", headers=auth_header(pm_token))
        assert resp.status_code == 403

    def test_pm_can_access_prosjekt(self, client, sample_docs, pm_token):
        resp = client.get("/api/docs/doc001", headers=auth_header(pm_token))
        assert resp.status_code == 200

    def test_pm_can_access_driftsmoter(self, client, sample_docs, pm_token):
        resp = client.get("/api/docs/doc003", headers=auth_header(pm_token))
        assert resp.status_code == 200

    def test_admin_sees_everything(self, client, sample_docs, admin_token):
        for doc_id in ["doc001", "doc002", "doc003"]:
            resp = client.get(f"/api/docs/{doc_id}", headers=auth_header(admin_token))
            assert resp.status_code == 200

    def test_hr_cannot_preview_prosjekt(self, client, sample_docs, hr_token):
        resp = client.get("/api/docs/doc001/preview", headers=auth_header(hr_token))
        assert resp.status_code == 403

    def test_hr_cannot_download_prosjekt(self, client, sample_docs, hr_token):
        resp = client.get("/api/docs/doc001/download", headers=auth_header(hr_token))
        assert resp.status_code == 403
