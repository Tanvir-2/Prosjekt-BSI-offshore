import pytest
import time
import os


@pytest.fixture(autouse=True)
def indexed_driftsmoter():
    """Index Driftsmøter folder before each test (fast — 15 files)."""
    from services.meili_service import delete_index, setup_index, bulk_index
    from config import DATA_FOLDER
    delete_index()
    setup_index()
    time.sleep(0.5)
    drift_path = os.path.join(DATA_FOLDER, "Driftsmøter")
    bulk_index(drift_path)
    yield
    delete_index()


class TestBasicSearch:
    """Tests for basic search queries."""

    def test_search_returns_results(self):
        from services.meili_service import search_documents
        results = search_documents("weekly")
        assert len(results["hits"]) > 0

    def test_search_empty_query_returns_all(self):
        from services.meili_service import search_documents, get_document_count
        results = search_documents("")
        assert len(results["hits"]) == get_document_count()

    def test_search_result_has_required_fields(self):
        from services.meili_service import search_documents
        results = search_documents("weekly")
        hit = results["hits"][0]
        assert "id" in hit
        assert "file_name" in hit
        assert "department" in hit
        assert "file_type" in hit

    def test_search_result_has_highlights(self):
        from services.meili_service import search_documents
        results = search_documents("weekly")
        hit = results["hits"][0]
        assert "_formatted" in hit
        assert "file_name" in hit["_formatted"]

    def test_search_returns_query(self):
        from services.meili_service import search_documents
        results = search_documents("project")
        assert results["query"] == "project"

    def test_search_has_total_count(self):
        from services.meili_service import search_documents
        results = search_documents("weekly")
        assert "estimatedTotalHits" in results


class TestTypoTolerance:
    """Tests for typo-tolerant search."""

    def test_typo_in_query_finds_results(self):
        """'weekli' (typo) should still find 'weekly' documents."""
        from services.meili_service import search_documents
        results = search_documents("weekli")
        assert len(results["hits"]) > 0


class TestFilters:
    """Tests for search with filters."""

    def test_filter_by_file_type_returns_all(self):
        from services.meili_service import search_documents
        results = search_documents("", filters=["file_type = pdf"])
        assert len(results["hits"]) == 15

    def test_filter_by_file_type(self):
        from services.meili_service import search_documents
        results = search_documents("", filters=["file_type = pdf"])
        assert len(results["hits"]) == 15

    def test_filter_nonexistent_department(self):
        from services.meili_service import search_documents
        results = search_documents("", filters=["department = HR"])
        assert len(results["hits"]) == 0

    def test_combined_filters(self):
        from services.meili_service import search_documents
        results = search_documents(
            "weekly",
            filters=["file_type = pdf"]
        )
        assert len(results["hits"]) > 0


class TestPagination:
    """Tests for pagination (limit + offset)."""

    def test_default_limit(self):
        from services.meili_service import search_documents
        results = search_documents("")
        assert len(results["hits"]) <= 20

    def test_custom_limit(self):
        from services.meili_service import search_documents
        results = search_documents("", limit=5)
        assert len(results["hits"]) == 5

    def test_offset(self):
        from services.meili_service import search_documents
        page1 = search_documents("", limit=5, offset=0)
        page2 = search_documents("", limit=5, offset=5)
        # Pages should have different documents
        ids1 = {h["id"] for h in page1["hits"]}
        ids2 = {h["id"] for h in page2["hits"]}
        assert len(ids1 & ids2) == 0

    def test_limit_one(self):
        from services.meili_service import search_documents
        results = search_documents("", limit=1)
        assert len(results["hits"]) == 1


class TestSorting:
    """Tests for sorting results."""

    def test_sort_by_created_at_desc(self):
        from services.meili_service import search_documents
        results = search_documents("", sort=["created_at:desc"])
        assert len(results["hits"]) > 0

    def test_sort_by_file_size_asc(self):
        from services.meili_service import search_documents
        results = search_documents("", sort=["file_size:asc"])
        sizes = [h["file_size"] for h in results["hits"]]
        assert sizes == sorted(sizes)


class TestDepartmentFilterByRole:
    """Tests for role-based department filtering."""

    def test_admin_sees_all(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("admin")
        assert result is None

    def test_hr_sees_hr_and_driftsmoter(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("hr")
        assert result is not None
        assert "HR" in result[0]
        assert "Driftsmøter" in result[0]

    def test_pm_sees_prosjekt_and_driftsmoter(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("project_manager")
        assert result is not None
        assert "Prosjekt" in result[0]
        assert "Driftsmøter" in result[0]

    def test_hr_cannot_see_prosjekt(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("hr")
        assert "Prosjekt" not in result[0]

    def test_pm_cannot_see_hr(self):
        from services.meili_service import get_department_filter
        result = get_department_filter("project_manager")
        assert "HR" not in result[0]
