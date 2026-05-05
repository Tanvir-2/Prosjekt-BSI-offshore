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


class TestEmptyQuery:
    """Tests for empty/whitespace query — browse all docs."""

    def test_empty_string_returns_all(self):
        from services.meili_service import search_documents, get_document_count
        results = search_documents("")
        assert len(results["hits"]) == get_document_count()

    def test_whitespace_only_returns_all(self):
        from services.meili_service import search_documents, get_document_count
        results = search_documents("   ")
        assert len(results["hits"]) == get_document_count()

    def test_empty_query_no_error(self):
        from services.meili_service import search_documents
        results = search_documents("")
        assert "hits" in results


class TestTypoTolerance:
    """Tests for typo-tolerant search behavior."""

    def test_one_typo_finds_results(self):
        """'weekli' should match 'weekly' (1 typo)."""
        from services.meili_service import search_documents
        results = search_documents("weekli")
        assert len(results["hits"]) > 0

    def test_case_insensitive(self):
        """Search should be case insensitive."""
        from services.meili_service import search_documents
        lower = search_documents("weekly")
        upper = search_documents("WEEKLY")
        assert len(lower["hits"]) == len(upper["hits"])

    def test_partial_word_match(self):
        """Prefix matching should work."""
        from services.meili_service import search_documents
        results = search_documents("week")
        assert len(results["hits"]) > 0


class TestSpecialCharacters:
    """Tests for queries with special characters."""

    def test_norwegian_characters(self):
        """Norwegian chars (æ, ø, å) should work in queries."""
        from services.meili_service import search_documents
        results = search_documents("møter")
        assert "hits" in results

    def test_numbers_in_query(self):
        from services.meili_service import search_documents
        results = search_documents("2024")
        assert "hits" in results

    def test_special_chars_no_crash(self):
        """Special regex-like chars should not crash the search."""
        from services.meili_service import search_documents
        for query in ["test+", "file.exe", "report (1)", "doc_v2", "a&b"]:
            results = search_documents(query)
            assert "hits" in results

    def test_very_long_query(self):
        """Very long query should not crash."""
        from services.meili_service import search_documents
        long_query = "a" * 500
        results = search_documents(long_query)
        assert "hits" in results
        assert len(results["hits"]) == 0  # Won't match anything


class TestPaginationEdgeCases:
    """Tests for pagination edge cases."""

    def test_offset_beyond_results(self):
        """Offset larger than total results should return empty."""
        from services.meili_service import search_documents
        results = search_documents("", offset=1000)
        assert len(results["hits"]) == 0

    def test_limit_zero_returns_nothing(self):
        """Limit 0 should return no hits."""
        from services.meili_service import search_documents
        results = search_documents("", limit=0)
        assert len(results["hits"]) == 0

    def test_limit_one(self):
        from services.meili_service import search_documents
        results = search_documents("", limit=1)
        assert len(results["hits"]) == 1

    def test_offset_zero_same_as_no_offset(self):
        from services.meili_service import search_documents
        r1 = search_documents("", limit=5, offset=0)
        r2 = search_documents("", limit=5)
        assert [h["id"] for h in r1["hits"]] == [h["id"] for h in r2["hits"]]

    def test_pagination_covers_all_docs(self):
        """Paginating through all results should cover every document."""
        from services.meili_service import search_documents, get_document_count
        total = get_document_count()
        all_ids = set()
        offset = 0
        while offset < total:
            results = search_documents("", limit=5, offset=offset)
            for hit in results["hits"]:
                all_ids.add(hit["id"])
            offset += 5
        assert len(all_ids) == total


class TestSearchResultOrdering:
    """Tests that results come back with expected structure."""

    def test_hits_have_unique_ids(self):
        from services.meili_service import search_documents
        results = search_documents("")
        ids = [h["id"] for h in results["hits"]]
        assert len(ids) == len(set(ids))

    def test_all_hits_have_department(self):
        from services.meili_service import search_documents
        results = search_documents("")
        for hit in results["hits"]:
            assert "department" in hit
            assert isinstance(hit["department"], str)
            assert len(hit["department"]) > 0

    def test_format_response_with_edge_cases(self):
        """format_search_response handles empty results gracefully."""
        from services.meili_service import search_documents, format_search_response
        raw = search_documents("xyznonexistent12345")
        response = format_search_response(raw, query="xyznonexistent12345")
        assert response["results"] == []
        assert response["total_hits"] == 0
