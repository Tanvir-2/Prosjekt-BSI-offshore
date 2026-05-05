import os
import pytest
from pathlib import Path


class TestSyntheticFixtures:
    """Verify all synthetic test fixture files exist and are non-empty."""

    @pytest.fixture
    def fixtures(self):
        from tests.fixtures import (
            SAMPLE_PDF, SAMPLE_DOCX, SAMPLE_DOTX, SAMPLE_XLSX,
            SAMPLE_XLSM, SAMPLE_PPTX, SAMPLE_JPG, SAMPLE_ZIP,
            EMPTY_PDF, EMPTY_DOCX, EMPTY_XLSX, CORRUPTED_PDF,
        )
        return {
            "pdf": SAMPLE_PDF,
            "docx": SAMPLE_DOCX,
            "dotx": SAMPLE_DOTX,
            "xlsx": SAMPLE_XLSX,
            "xlsm": SAMPLE_XLSM,
            "pptx": SAMPLE_PPTX,
            "jpg": SAMPLE_JPG,
            "zip": SAMPLE_ZIP,
            "empty_pdf": EMPTY_PDF,
            "empty_docx": EMPTY_DOCX,
            "empty_xlsx": EMPTY_XLSX,
            "corrupted_pdf": CORRUPTED_PDF,
        }

    def test_all_synthetic_files_exist(self, fixtures):
        for name, path in fixtures.items():
            assert os.path.isfile(path), f"Missing fixture: {name} at {path}"

    def test_synthetic_files_non_empty(self, fixtures):
        for name, path in fixtures.items():
            size = os.path.getsize(path)
            assert size > 0, f"Empty fixture: {name}"

    def test_sample_pdf_has_pdf_header(self):
        """sample.pdf should start with PDF magic bytes."""
        from tests.fixtures import SAMPLE_PDF
        with open(SAMPLE_PDF, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_sample_docx_is_zip(self):
        """sample.docx should be a valid ZIP (DOCX is a ZIP archive)."""
        import zipfile
        from tests.fixtures import SAMPLE_DOCX
        assert zipfile.is_zipfile(SAMPLE_DOCX)

    def test_sample_xlsx_is_zip(self):
        """sample.xlsx should be a valid ZIP (XLSX is a ZIP archive)."""
        import zipfile
        from tests.fixtures import SAMPLE_XLSX
        assert zipfile.is_zipfile(SAMPLE_XLSX)

    def test_sample_pptx_is_zip(self):
        """sample.pptx should be a valid ZIP (PPTX is a ZIP archive)."""
        import zipfile
        from tests.fixtures import SAMPLE_PPTX
        assert zipfile.is_zipfile(SAMPLE_PPTX)

    def test_sample_jpg_is_valid(self):
        """sample.jpg should be a valid image."""
        from PIL import Image
        from tests.fixtures import SAMPLE_JPG
        img = Image.open(SAMPLE_JPG)
        assert img.size == (10, 10)

    def test_sample_zip_is_valid(self):
        """sample.zip should be a valid zip archive."""
        import zipfile
        from tests.fixtures import SAMPLE_ZIP
        with zipfile.ZipFile(SAMPLE_ZIP) as zf:
            assert len(zf.namelist()) >= 1

    def test_empty_pdf_has_pdf_header(self):
        """empty.pdf should be a valid PDF file."""
        from tests.fixtures import EMPTY_PDF
        with open(EMPTY_PDF, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"


class TestRealBSIFiles:
    """Verify all real BSI data files exist and are accessible."""

    @pytest.fixture
    def real_files(self):
        from tests.fixtures import (
            REAL_PDF, REAL_DOCX, REAL_XLSX, REAL_XLS, REAL_PPTX,
            REAL_MSG, REAL_JPG, REAL_HEIC, REAL_DOC, REAL_MOV,
            REAL_ZIP, REAL_LNK,
        )
        return {
            "pdf": REAL_PDF,
            "docx": REAL_DOCX,
            "xlsx": REAL_XLSX,
            "xls": REAL_XLS,
            "pptx": REAL_PPTX,
            "msg": REAL_MSG,
            "jpg": REAL_JPG,
            "heic": REAL_HEIC,
            "doc": REAL_DOC,
            "mov": REAL_MOV,
            "zip": REAL_ZIP,
            "lnk": REAL_LNK,
        }

    def test_all_real_files_exist(self, real_files):
        for name, path in real_files.items():
            assert os.path.isfile(path), f"Missing real BSI file: {name} at {path}"

    def test_all_real_files_readable(self, real_files):
        for name, path in real_files.items():
            assert os.access(path, os.R_OK), f"Cannot read: {name}"

    def test_real_pdf_has_content(self):
        from tests.fixtures import REAL_PDF
        assert os.path.getsize(REAL_PDF) > 100
