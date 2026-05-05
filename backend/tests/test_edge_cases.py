import os
import pytest


class TestCorruptedFiles:
    """Edge case: corrupted files should not crash, just log error."""

    def test_corrupted_pdf_build_document(self):
        from services.ingestion import build_document
        from tests.fixtures import CORRUPTED_PDF

        doc = build_document(CORRUPTED_PDF)
        
        assert doc is not None
        assert doc["file_name"] == "corrupted.pdf"


class TestMixedCaseExtensions:
    """Edge case: real BSI data has .JPG, .PDF, .XLSX, .Pdf, .DOCX, .HEIC."""

    def test_uppercase_pdf(self):
        from services.ingestion import build_document
        from pathlib import Path

       
        from config import DATA_FOLDER
        for root, dirs, files in os.walk(DATA_FOLDER):
            for f in files:
                if f.endswith(".PDF"):
                    path = os.path.join(root, f)
                    doc = build_document(path)
                    assert doc is not None
                    assert doc["file_type"] == ".pdf".lstrip(".")  # normalized to lowercase
                    return
        pytest.skip("No .PDF (uppercase) file found")

    def test_uppercase_jpg(self):
        from services.ingestion import build_document

        from config import DATA_FOLDER
        for root, dirs, files in os.walk(DATA_FOLDER):
            for f in files:
                if f.endswith(".JPG"):
                    path = os.path.join(root, f)
                    doc = build_document(path)
                    assert doc is not None
                    return
        pytest.skip("No .JPG (uppercase) file found")

    def test_mixed_case_pdf(self):
        from services.ingestion import build_document

        from config import DATA_FOLDER
        for root, dirs, files in os.walk(DATA_FOLDER):
            for f in files:
                if f.endswith(".Pdf"):
                    path = os.path.join(root, f)
                    doc = build_document(path)
                    assert doc is not None
                    assert doc["file_type"] == "pdf"
                    return
        pytest.skip("No .Pdf (mixed case) file found")


class TestSpecialCharactersInNames:
    """Edge case: Norwegian characters and special chars in filenames."""

    def test_norwegian_characters_in_filename(self):
        from services.ingestion import build_document
        from config import DATA_FOLDER

        
        for root, dirs, files in os.walk(DATA_FOLDER):
            for f in files:
                if any(c in f for c in "æøåÆØÅ"):
                    path = os.path.join(root, f)
                    doc = build_document(path)
                    assert doc is not None
                    assert doc["file_name"] == f
                    return
        pytest.skip("No file with Norwegian characters found")

    def test_special_chars_in_folder_path(self):
        """Driftsmøter has ø in the folder name itself."""
        from services.ingestion import extract_department
        from config import DATA_FOLDER

        dept = extract_department(
            os.path.join(DATA_FOLDER, "Driftsmøter", "test.pdf"),
            DATA_FOLDER
        )
        assert dept == "Driftsmøter"


class TestNonexistentFiles:
    """Edge case: files that don't exist."""

    def test_nonexistent_file_build_document(self):
        from services.ingestion import build_document

        with pytest.raises(FileNotFoundError):
            build_document("/nonexistent/path/file.pdf")


class TestFullScanSanity:
    """Sanity check: scan all departments and verify counts."""

    def test_total_file_count(self):
        from services.ingestion import scan_directory
        from config import DATA_FOLDER

        docs = scan_directory(DATA_FOLDER)
        
        assert len(docs) == 1614

    def test_no_lnk_files_in_results(self):
        from services.ingestion import scan_directory
        from config import DATA_FOLDER

        docs = scan_directory(DATA_FOLDER)
        lnk_docs = [d for d in docs if d["file_type"] == "lnk"]
        assert len(lnk_docs) == 0

    def test_all_docs_have_valid_ids(self):
        from services.ingestion import scan_directory
        from config import DATA_FOLDER

        docs = scan_directory(DATA_FOLDER)
        for doc in docs:
            assert len(doc["id"]) == 12
            assert all(c in "0123456789abcdef" for c in doc["id"])

    def test_unique_ids(self):
        """All document IDs should be unique."""
        from services.ingestion import scan_directory
        from config import DATA_FOLDER

        docs = scan_directory(DATA_FOLDER)
        ids = [d["id"] for d in docs]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {len(ids)} total, {len(set(ids))} unique"
