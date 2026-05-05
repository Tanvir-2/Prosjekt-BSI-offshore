import pytest
import time
import os


@pytest.fixture(autouse=True)
def clean_index():
    """Fresh index for each test."""
    from services.meili_service import delete_index, setup_index
    delete_index()
    setup_index()
    time.sleep(0.5)
    yield
    delete_index()


class TestBulkIndexDriftsmoter:
    """Bulk index the Driftsmøter folder (15 files — fast test)."""

    def test_bulk_index_count(self):
        from services.meili_service import bulk_index, get_document_count
        from config import DATA_FOLDER

        drift_path = os.path.join(DATA_FOLDER, "Driftsmøter")
        total = bulk_index(drift_path)
        assert total == 15
        assert get_document_count() == 15

    def test_all_documents_searchable(self):
        from services.meili_service import bulk_index, get_index
        from config import DATA_FOLDER

        drift_path = os.path.join(DATA_FOLDER, "Driftsmøter")
        bulk_index(drift_path)

        results = get_index().search("weekly")
        assert len(results["hits"]) > 0

    def test_documents_have_correct_file_type(self):
        from services.meili_service import bulk_index, get_index
        from config import DATA_FOLDER

        drift_path = os.path.join(DATA_FOLDER, "Driftsmøter")
        bulk_index(drift_path)

        results = get_index().search("", {"limit": 20})
        for hit in results["hits"]:
            assert hit["file_type"] == "pdf"


class TestBulkIndexFull:
    """Bulk index all BSI files (slower — tests the real dataset)."""

    def test_full_bulk_index_count(self):
        from services.meili_service import bulk_index, get_document_count
        from config import DATA_FOLDER

        total = bulk_index(DATA_FOLDER)
        assert total == 1614
        assert get_document_count() == 1614

    def test_department_filter_works(self):
        from services.meili_service import bulk_index, get_index
        from config import DATA_FOLDER

        bulk_index(DATA_FOLDER)

        hr_results = get_index().search("", {"filter": "department = HR"})
        assert hr_results["estimatedTotalHits"] > 0

        prosjekt_results = get_index().search("", {"filter": "department = Prosjekt"})
        assert prosjekt_results["estimatedTotalHits"] >= 1000

    def test_file_type_filter(self):
        from services.meili_service import bulk_index, get_index
        from config import DATA_FOLDER

        bulk_index(DATA_FOLDER)

        pdf_results = get_index().search("", {"filter": "file_type = pdf"})
        assert pdf_results["estimatedTotalHits"] > 500

        msg_results = get_index().search("", {"filter": "file_type = msg"})
        assert msg_results["estimatedTotalHits"] > 100
