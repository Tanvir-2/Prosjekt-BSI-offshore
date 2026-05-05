import os
import pytest
from pathlib import Path


class TestGenerateId:
    """Tests for generate_id function."""

    def test_returns_12_char_hex(self):
        from services.ingestion import generate_id
        result = generate_id("/some/file.pdf")
        assert len(result) == 12
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        from services.ingestion import generate_id
        assert generate_id("/same/path.pdf") == generate_id("/same/path.pdf")

    def test_different_paths_different_ids(self):
        from services.ingestion import generate_id
        assert generate_id("/path/a.pdf") != generate_id("/path/b.pdf")


class TestExtractDepartment:
    """Tests for extract_department function."""

    def test_extracts_prosjekt(self):
        from services.ingestion import extract_department
        result = extract_department(
            "/data/Prosjekt/Prosjekter 2023/3086/report.pdf",
            data_root="/data"
        )
        assert result == "Prosjekt"

    def test_extracts_hr(self):
        from services.ingestion import extract_department
        result = extract_department(
            "/data/HR/HMS/policy.pdf",
            data_root="/data"
        )
        assert result == "HR"

    def test_extracts_driftsmoter(self):
        from services.ingestion import extract_department
        result = extract_department(
            "/data/Driftsmøter/week3.pdf",
            data_root="/data"
        )
        assert result == "Driftsmøter"

    def test_works_with_real_data(self):
        from services.ingestion import extract_department
        from config import DATA_FOLDER
        from tests.fixtures import REAL_PDF

        result = extract_department(REAL_PDF, DATA_FOLDER)
        assert result == "Prosjekt"


class TestGetFileMetadata:
    """Tests for get_file_metadata function."""

    def test_returns_file_size(self):
        from services.ingestion import get_file_metadata
        from tests.fixtures import SAMPLE_PDF

        result = get_file_metadata(SAMPLE_PDF)
        assert result["file_size"] > 0

    def test_returns_created_at(self):
        from services.ingestion import get_file_metadata
        from tests.fixtures import SAMPLE_PDF

        result = get_file_metadata(SAMPLE_PDF)
        assert "created_at" in result
        assert len(result["created_at"]) == 10  # YYYY-MM-DD

    def test_returns_modified_at(self):
        from services.ingestion import get_file_metadata
        from tests.fixtures import SAMPLE_PDF

        result = get_file_metadata(SAMPLE_PDF)
        assert "modified_at" in result
        assert len(result["modified_at"]) == 10

    def test_dates_are_valid(self):
        from services.ingestion import get_file_metadata
        from tests.fixtures import SAMPLE_PDF

        result = get_file_metadata(SAMPLE_PDF)
        from datetime import datetime
        # Should not raise
        datetime.strptime(result["created_at"], "%Y-%m-%d")
        datetime.strptime(result["modified_at"], "%Y-%m-%d")


class TestBuildDocument:
    """Tests for build_document function."""

    def test_builds_pdf_document(self):
        from services.ingestion import build_document
        from tests.fixtures import SAMPLE_PDF

        doc = build_document(SAMPLE_PDF)
        assert doc is not None
        assert doc["file_name"] == "sample.pdf"
        assert doc["file_type"] == "pdf"

    def test_builds_image_document(self):
        from services.ingestion import build_document
        from tests.fixtures import SAMPLE_JPG

        doc = build_document(SAMPLE_JPG)
        assert doc is not None
        assert doc["file_name"] == "sample.jpg"

    def test_builds_zip_document(self):
        from services.ingestion import build_document
        from tests.fixtures import SAMPLE_ZIP

        doc = build_document(SAMPLE_ZIP)
        assert doc is not None

    def test_skips_lnk_files(self):
        from services.ingestion import build_document
        from tests.fixtures import REAL_LNK

        doc = build_document(REAL_LNK)
        assert doc is None

    def test_document_has_all_required_fields(self):
        from services.ingestion import build_document
        from tests.fixtures import SAMPLE_PDF

        doc = build_document(SAMPLE_PDF)
        required_fields = {
            "id", "file_name", "file_path", "file_type",
            "department", "file_size", "created_at", "modified_at",
            "restricted"
        }
        assert set(doc.keys()) == required_fields

    def test_id_is_12_char_hex(self):
        from services.ingestion import build_document
        from tests.fixtures import SAMPLE_PDF

        doc = build_document(SAMPLE_PDF)
        assert len(doc["id"]) == 12
        assert all(c in "0123456789abcdef" for c in doc["id"])

    def test_restricted_defaults_false(self):
        from services.ingestion import build_document
        from tests.fixtures import SAMPLE_PDF

        doc = build_document(SAMPLE_PDF)
        assert doc["restricted"] is False


class TestBuildDocumentRealBSI:
    """Integration tests with real BSI files."""

    def test_real_pdf_document(self):
        from services.ingestion import build_document
        from config import DATA_FOLDER
        from tests.fixtures import REAL_PDF

        doc = build_document(REAL_PDF, DATA_FOLDER)
        assert doc["department"] == "Prosjekt"
        assert doc["file_type"] == "pdf"

    def test_real_heic_document(self):
        from services.ingestion import build_document
        from config import DATA_FOLDER
        from tests.fixtures import REAL_HEIC

        doc = build_document(REAL_HEIC, DATA_FOLDER)
        assert doc["file_type"] == "heic"


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scans_driftsmoter_folder(self):
        from services.ingestion import scan_directory
        from config import DATA_FOLDER

        drift_path = os.path.join(DATA_FOLDER, "Driftsmøter")
        docs = scan_directory(drift_path)
        assert len(docs) == 15  # 15 weekly report PDFs
        for doc in docs:
            assert doc["file_type"] == "pdf"

    def test_scan_results_are_valid_documents(self):
        from services.ingestion import scan_directory
        from config import DATA_FOLDER

        drift_path = os.path.join(DATA_FOLDER, "Driftsmøter")
        docs = scan_directory(drift_path)
        required = {"id", "file_name", "file_path", "file_type", "department",
                     "file_size", "created_at", "modified_at", "restricted"}
        for doc in docs:
            assert set(doc.keys()) == required
