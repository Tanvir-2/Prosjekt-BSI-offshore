import pytest
import time
import os


@pytest.fixture(scope="module")
def full_index():
    """Index all BSI files once for the whole module (slow, ~90s)."""
    from services.meili_service import delete_index, setup_index, bulk_index
    from config import DATA_FOLDER
    delete_index()
    setup_index()
    time.sleep(0.5)
    total = bulk_index(DATA_FOLDER)
    yield total
    delete_index()


class TestAdminRoleSearch:
    """Admin sees all departments — no filter applied."""

    def test_admin_filter_is_none(self):
        from services.meili_service import get_department_filter
        assert get_department_filter("admin") is None

    def test_admin_searches_all_departments(self, full_index):
        from services.meili_service import get_document_count
        assert get_document_count() >= 1614

    def test_admin_finds_hr_docs(self, full_index):
        from services.meili_service import search_documents
        results = search_documents("", filters=["department = HR"])
        assert results["estimatedTotalHits"] > 0

    def test_admin_finds_prosjekt_docs(self, full_index):
        from services.meili_service import search_documents
        results = search_documents("", filters=["department = Prosjekt"])
        assert results["estimatedTotalHits"] >= 1000

    def test_admin_finds_driftsmoter_docs(self, full_index):
        from services.meili_service import search_documents
        results = search_documents("", filters=["department = Driftsmøter"])
        assert results["estimatedTotalHits"] > 0


class TestHRRoleSearch:
    """HR user can only search HR + Driftsmøter departments."""

    def test_hr_filter_format(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("hr")
        assert result is not None
        assert "HR" in result[0]
        assert "Driftsmøter" in result[0]

    def test_hr_sees_hr_docs(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("hr")
        results = search_documents("", filters=role_filter, limit=2000)
        departments = {h["department"] for h in results["hits"]}
        assert "HR" in departments

    def test_hr_sees_driftsmoter_docs(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("hr")
        results = search_documents("", filters=role_filter, limit=2000)
        departments = {h["department"] for h in results["hits"]}
        assert "Driftsmøter" in departments

    def test_hr_cannot_see_prosjekt_docs(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("hr")
        results = search_documents("", filters=role_filter, limit=2000)
        departments = {h["department"] for h in results["hits"]}
        assert "Prosjekt" not in departments

    def test_hr_total_less_than_admin(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("hr")
        hr_results = search_documents("", filters=role_filter, limit=2000)
        all_results = search_documents("", limit=2000)
        assert hr_results["estimatedTotalHits"] < all_results["estimatedTotalHits"]


class TestPMRoleSearch:
    """Project Manager can only search Prosjekt + Driftsmøter departments."""

    def test_pm_filter_format(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("project_manager")
        assert result is not None
        assert "Prosjekt" in result[0]
        assert "Driftsmøter" in result[0]

    def test_pm_sees_prosjekt_docs(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("project_manager")
        results = search_documents("", filters=role_filter, limit=2000)
        departments = {h["department"] for h in results["hits"]}
        assert "Prosjekt" in departments

    def test_pm_sees_driftsmoter_docs(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("project_manager")
        results = search_documents("", filters=role_filter, limit=2000)
        departments = {h["department"] for h in results["hits"]}
        assert "Driftsmøter" in departments

    def test_pm_cannot_see_hr_docs(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("project_manager")
        results = search_documents("", filters=role_filter, limit=2000)
        departments = {h["department"] for h in results["hits"]}
        assert "HR" not in departments

    def test_pm_total_less_than_admin(self, full_index):
        from services.meili_service import search_documents, get_department_filter, get_document_count
        role_filter = get_department_filter("project_manager")
        pm_results = search_documents("", filters=role_filter, limit=2000)
        total_in_index = get_document_count()
        assert pm_results["estimatedTotalHits"] < total_in_index


class TestDriftsmoterVisibleToAll:
    """Driftsmøter (meeting notes) should be visible to all roles."""

    def test_driftsmoter_visible_to_hr(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("hr")
        results = search_documents("", filters=role_filter, limit=2000)
        drift_docs = [h for h in results["hits"] if h["department"] == "Driftsmøter"]
        assert len(drift_docs) > 0

    def test_driftsmoter_visible_to_pm(self, full_index):
        from services.meili_service import search_documents, get_department_filter
        role_filter = get_department_filter("project_manager")
        results = search_documents("", filters=role_filter, limit=2000)
        drift_docs = [h for h in results["hits"] if h["department"] == "Driftsmøter"]
        assert len(drift_docs) > 0

    def test_driftsmoter_visible_to_admin(self, full_index):
        from services.meili_service import search_documents
        results = search_documents("", filters=["department = Driftsmøter"])
        assert results["estimatedTotalHits"] > 0
