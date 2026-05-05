import pytest
from fastapi.testclient import TestClient

from services.auth import create_token
from services.meili_service import setup_index, add_document, delete_index


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a TestClient for search endpoint testing."""
    from main import app
    from database import engine, Base
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def clean_index():
    """Provide a clean Meilisearch index for search tests."""
    delete_index()
    setup_index()
    yield
    
    delete_index()
    setup_index()


@pytest.fixture
def sample_docs(clean_index):
    """Add sample documents to the index for search tests."""
    docs = [
        {
            "id": "test001",
            "file_name": "transocean_report.pdf",
            "file_path": "/data/Prosjekt/Prosjekter 2023/3086 Transocean/report.pdf",
            "department": "Prosjekt",
            "file_type": "pdf",
            "file_size": 245600,
            "created_at": "2023-01-15",
            "modified_at": "2023-03-20",
            "restricted": False,
        },
        {
            "id": "test002",
            "file_name": "hr_policy.docx",
            "file_path": "/data/HR/Policies/hr_policy.docx",
            "department": "HR",
            "file_type": "docx",
            "file_size": 88000,
            "created_at": "2023-02-01",
            "modified_at": "2023-04-10",
            "restricted": False,
        },
        {
            "id": "test003",
            "file_name": "survey_photo.jpg",
            "file_path": "/data/Prosjekt/Prosjekter 2023/3086 Transocean/photo.jpg",
            "department": "Prosjekt",
            "file_type": "jpg",
            "file_size": 3200000,
            "created_at": "2023-02-10",
            "modified_at": "2023-02-10",
            "restricted": False,
        },
        {
            "id": "test004",
            "file_name": "meeting_notes.docx",
            "file_path": "/data/Driftsmøter/meeting_notes.docx",
            "department": "Driftsmøter",
            "file_type": "docx",
            "file_size": 45000,
            "created_at": "2023-03-01",
            "modified_at": "2023-03-01",
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




class TestSearchBasic:
    def test_search_returns_results(self, client, sample_docs, admin_token):
        resp = client.get("/api/search?q=transocean", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "transocean"
        assert data["total_hits"] >= 1
        assert len(data["results"]) >= 1

    def test_search_empty_query(self, client, sample_docs, admin_token):
        resp = client.get("/api/search", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hits"] >= 4  

    def test_search_no_results(self, client, sample_docs, admin_token):
        resp = client.get("/api/search?q=zzzznonexistent", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["total_hits"] == 0

    def test_search_requires_auth(self, client, sample_docs):
        resp = client.get("/api/search?q=test")
        assert resp.status_code == 401

    def test_search_result_fields(self, client, sample_docs, admin_token):
        resp = client.get("/api/search?q=transocean", headers=auth_header(admin_token))
        result = resp.json()["results"][0]
        for field in ["id", "file_name", "department", "file_type",
                       "file_size", "created_at", "modified_at", "highlight"]:
            assert field in result




class TestSearchFilters:
    def test_filter_by_file_type(self, client, sample_docs, admin_token):
        resp = client.get("/api/search?file_type=pdf", headers=auth_header(admin_token))
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["file_type"] == "pdf"

    def test_filter_by_department(self, client, sample_docs, admin_token):
        resp = client.get("/api/search?department=HR", headers=auth_header(admin_token))
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["department"] == "HR"

    def test_filter_date_range(self, client, sample_docs, admin_token):
        resp = client.get(
            "/api/search?date_from=2023-02-01&date_to=2023-02-28",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    def test_combined_filters(self, client, sample_docs, admin_token):
        resp = client.get(
            "/api/search?q=report&file_type=pdf&department=Prosjekt",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200




class TestSearchRoleAccess:
    def test_admin_sees_all_departments(self, client, sample_docs, admin_token):
        resp = client.get("/api/search", headers=auth_header(admin_token))
        departments = {r["department"] for r in resp.json()["results"]}
        assert "Prosjekt" in departments
        assert "HR" in departments
        assert "Driftsmøter" in departments

    def test_hr_sees_only_hr_and_driftsmoter(self, client, sample_docs, hr_token):
        resp = client.get("/api/search", headers=auth_header(hr_token))
        departments = {r["department"] for r in resp.json()["results"]}
        assert "HR" in departments
        assert "Driftsmøter" in departments
        assert "Prosjekt" not in departments

    def test_pm_sees_only_prosjekt_and_driftsmoter(self, client, sample_docs, pm_token):
        resp = client.get("/api/search", headers=auth_header(pm_token))
        departments = {r["department"] for r in resp.json()["results"]}
        assert "Prosjekt" in departments
        assert "Driftsmøter" in departments
        assert "HR" not in departments




class TestSearchPagination:
    def test_pagination_limit(self, client, sample_docs, admin_token):
        resp = client.get("/api/search?limit=2", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 2

    def test_pagination_offset(self, client, sample_docs, admin_token):
        resp1 = client.get("/api/search?limit=2&offset=0", headers=auth_header(admin_token))
        resp2 = client.get("/api/search?limit=2&offset=2", headers=auth_header(admin_token))
        ids1 = {r["id"] for r in resp1.json()["results"]}
        ids2 = {r["id"] for r in resp2.json()["results"]}
        assert ids1.isdisjoint(ids2)  

    def test_sort_by_date(self, client, sample_docs, admin_token):
        resp = client.get(
            "/api/search?sort_by=created_at&sort_order=desc",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        if len(results) >= 2:
            assert results[0]["created_at"] >= results[1]["created_at"]




class TestSuggest:
    def test_suggest_returns_fewer_results(self, client, sample_docs, admin_token):
        resp = client.get("/api/search/suggest?q=trans", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 5  

    def test_suggest_respects_role(self, client, sample_docs, hr_token):
        resp = client.get("/api/search/suggest?q=trans", headers=auth_header(hr_token))
        departments = {r["department"] for r in resp.json()["results"]}
        assert "Prosjekt" not in departments

    def test_suggest_requires_auth(self, client, sample_docs):
        resp = client.get("/api/search/suggest?q=test")
        assert resp.status_code == 401

    def test_suggest_custom_limit(self, client, sample_docs, admin_token):
        resp = client.get("/api/search/suggest?q=a&limit=2", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 2
