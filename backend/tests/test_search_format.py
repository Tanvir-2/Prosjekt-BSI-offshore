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


class TestFormatSearchResponse:
    """Tests for format_search_response output structure."""

    def test_response_has_required_top_level_keys(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        assert "query" in response
        assert "total_hits" in response
        assert "limit" in response
        assert "offset" in response
        assert "results" in response

    def test_response_query_matches_input(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        assert response["query"] == "weekly"

    def test_total_hits_is_integer(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        assert isinstance(response["total_hits"], int)
        assert response["total_hits"] > 0

    def test_results_is_list(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        assert isinstance(response["results"], list)
        assert len(response["results"]) > 0

    def test_each_result_has_required_fields(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        required = [
            "id", "file_name", "department", "file_type",
            "file_size", "created_at", "modified_at", "highlight",
        ]
        for result in response["results"]:
            for field in required:
                assert field in result, f"Missing field: {field}"


class TestHighlight:
    """Tests for filename highlight extraction."""

    def test_highlight_is_string(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        for result in response["results"]:
            assert isinstance(result["highlight"], str)

    def test_highlight_contains_em_tags(self):
        """Filename match highlight should contain <em> tags."""
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("weekly")
        response = format_search_response(raw, query="weekly")
        if response["results"]:
            # At least one result should have highlighted filename
            highlights = [r["highlight"] for r in response["results"] if "<em>" in r["highlight"]]
            assert len(highlights) > 0

    def test_empty_query_returns_filename(self):
        """Empty query should return plain filename as highlight."""
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("")
        response = format_search_response(raw, query="")
        for result in response["results"]:
            assert isinstance(result["highlight"], str)
            assert len(result["highlight"]) > 0


class TestPaginationInResponse:
    """Tests for pagination metadata in formatted response."""

    def test_default_limit_and_offset(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("")
        response = format_search_response(raw, query="")
        assert response["limit"] == 20
        assert response["offset"] == 0

    def test_custom_limit_and_offset(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("", limit=5, offset=3)
        response = format_search_response(raw, query="")
        assert response["limit"] == 5
        assert response["offset"] == 3
        assert len(response["results"]) <= 5

    def test_results_count_matches_limit(self):
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("", limit=3)
        response = format_search_response(raw, query="")
        assert len(response["results"]) == 3
