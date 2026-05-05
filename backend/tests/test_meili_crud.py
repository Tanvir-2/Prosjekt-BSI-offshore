import pytest
import time


@pytest.fixture(autouse=True)
def clean_index():
    """Fresh index for each test."""
    from services.meili_service import delete_index, setup_index
    delete_index()
    setup_index()
    time.sleep(0.5)
    yield
    delete_index()


SAMPLE_DOC = {
    "id": "abc123",
    "file_name": "transocean_report.pdf",
    "file_path": "/data/Prosjekt/transocean_report.pdf",
    "file_type": "pdf",
    "department": "Prosjekt",
    "file_size": 245600,
    "created_at": "2023-01-15",
    "modified_at": "2023-03-20",
    "restricted": False,
}

SAMPLE_DOC_2 = {
    "id": "def456",
    "file_name": "hr_policy.docx",
    "file_path": "/data/HR/hr_policy.docx",
    "file_type": "docx",
    "department": "HR",
    "file_size": 50000,
    "created_at": "2023-02-10",
    "modified_at": "2023-02-10",
    "restricted": False,
}


class TestAddDocument:
    """Tests for adding a single document."""

    def test_add_single_document(self):
        from services.meili_service import add_document, get_document_count
        add_document(SAMPLE_DOC)
        assert get_document_count() == 1

    def test_add_and_retrieve_document(self):
        from services.meili_service import add_document, get_document
        add_document(SAMPLE_DOC)
        doc = get_document("abc123")
        assert doc["file_name"] == "transocean_report.pdf"
        assert doc["department"] == "Prosjekt"

    def test_add_document_preserves_all_fields(self):
        from services.meili_service import add_document, get_document
        add_document(SAMPLE_DOC)
        doc = get_document("abc123")
        for key in SAMPLE_DOC:
            assert key in doc

    def test_add_document_updates_existing(self):
        """Adding a doc with the same ID should update it."""
        from services.meili_service import add_document, get_document, get_document_count
        add_document(SAMPLE_DOC)

        updated = dict(SAMPLE_DOC)
        updated["file_name"] = "transocean_report_v2.pdf"
        add_document(updated)

        assert get_document_count() == 1  # still 1, not 2
        doc = get_document("abc123")
        assert doc["file_name"] == "transocean_report_v2.pdf"


class TestAddDocuments:
    """Tests for adding multiple documents at once."""

    def test_add_multiple_documents(self):
        from services.meili_service import add_documents, get_document_count
        add_documents([SAMPLE_DOC, SAMPLE_DOC_2])
        assert get_document_count() == 2

    def test_add_empty_list(self):
        """Adding empty list should not crash."""
        from services.meili_service import add_documents, get_document_count
        add_documents([])
        assert get_document_count() == 0


class TestRemoveDocument:
    """Tests for removing a document."""

    def test_remove_existing_document(self):
        from services.meili_service import add_document, remove_document, get_document_count
        add_document(SAMPLE_DOC)
        assert get_document_count() == 1

        remove_document("abc123")
        assert get_document_count() == 0

    def test_remove_nonexistent_document(self):
        """Removing a doc that doesn't exist should not crash."""
        from services.meili_service import remove_document
        remove_document("nonexistent_id")

    def test_remove_only_one_of_two(self):
        from services.meili_service import add_documents, remove_document, get_document, get_document_count
        add_documents([SAMPLE_DOC, SAMPLE_DOC_2])
        remove_document("abc123")
        assert get_document_count() == 1
        doc = get_document("def456")
        assert doc["file_name"] == "hr_policy.docx"


class TestGetDocument:
    """Tests for retrieving a document."""

    def test_get_existing_document(self):
        from services.meili_service import add_document, get_document
        add_document(SAMPLE_DOC)
        doc = get_document("abc123")
        assert doc["id"] == "abc123"

    def test_get_nonexistent_document_raises(self):
        from services.meili_service import get_document
        with pytest.raises(Exception):
            get_document("nonexistent_id")
