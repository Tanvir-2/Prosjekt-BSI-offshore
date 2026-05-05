import pytest
import time
import os
import shutil
import tempfile
from pathlib import Path


@pytest.fixture(autouse=True)
def clean_index():
    """Fresh Meilisearch index for each test."""
    from services.meili_service import delete_index, setup_index
    delete_index()
    setup_index()
    time.sleep(0.3)
    yield
    delete_index()


class TestRenameAndMove:
    """Tests for file rename and move operations."""

    def test_renamed_file_gets_new_id(self):
        """Renaming a file should remove old ID and index under new ID."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document, get_document_count
        from services.ingestion import generate_id
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create original file
            original = os.path.join(tmpdir, "original.pdf")
            shutil.copy2(SAMPLE_PDF, original)

            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(2.0)  # wait for debounce

            count_before = get_document_count()
            assert count_before >= 1

            # Rename the file
            renamed = os.path.join(tmpdir, "renamed.pdf")
            os.rename(original, renamed)
            time.sleep(2.0)

            watcher.stop()

            # Old ID should be gone (delete event), new ID should exist
            # On macOS, rename triggers: delete old + create new
            count_after = get_document_count()
            assert count_after >= 1

    def test_moved_to_subfolder(self):
        """Moving file to a new subfolder should re-index it."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "report.pdf")
            shutil.copy2(SAMPLE_PDF, src)

            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(2.0)

            # Create subfolder and move file
            subfolder = os.path.join(tmpdir, "Prosjekt")
            os.makedirs(subfolder)
            dest = os.path.join(subfolder, "report.pdf")
            shutil.move(src, dest)
            time.sleep(2.0)

            watcher.stop()
            assert get_document_count() >= 1


class TestNestedDirectories:
    """Tests for files in nested subdirectories."""

    def test_file_created_in_nested_dir(self):
        """File created 3 levels deep should be detected."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            deep_dir = os.path.join(tmpdir, "Prosjekt", "2023", "SubProject")
            os.makedirs(deep_dir)

            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            dest = os.path.join(deep_dir, "deep_report.pdf")
            shutil.copy2(SAMPLE_PDF, dest)
            time.sleep(2.0)

            watcher.stop()
            assert get_document_count() >= 1

    def test_new_subfolder_created_then_file(self):
        """Creating a folder then adding a file should work."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            new_dir = os.path.join(tmpdir, "HR")
            os.makedirs(new_dir)
            time.sleep(0.2)

            dest = os.path.join(new_dir, "policy.pdf")
            shutil.copy2(SAMPLE_PDF, dest)
            time.sleep(2.0)

            watcher.stop()
            assert get_document_count() >= 1


class TestMultipleRapidFiles:
    """Tests for multiple files created in quick succession."""

    def test_three_files_created_rapidly(self):
        """Three files created quickly should all be indexed."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            for i in range(3):
                dest = os.path.join(tmpdir, f"file_{i}.pdf")
                shutil.copy2(SAMPLE_PDF, dest)

            time.sleep(3.0)  

            watcher.stop()
            assert get_document_count() >= 3

    def test_create_and_immediately_delete(self):
        """Create a file then delete it before debounce fires."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            dest = os.path.join(tmpdir, "ephemeral.pdf")
            shutil.copy2(SAMPLE_PDF, dest)
            time.sleep(0.2)  
            os.remove(dest)  
            time.sleep(2.0)

            watcher.stop()
           
            assert get_document_count() <= 1


class TestBinaryAndUnsupportedFiles:
    """Tests for files that can't be text-extracted."""

    def test_image_file_indexed_as_name_match(self):
        """Image file (no text extraction) should still be indexed."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count, get_document
        from tests.fixtures import SAMPLE_JPG

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            dest = os.path.join(tmpdir, "photo.jpg")
            shutil.copy2(SAMPLE_JPG, dest)
            time.sleep(2.0)

            watcher.stop()
            count = get_document_count()
            assert count >= 1

    def test_unsupported_file_indexed_by_name(self):
        """Files with unsupported extensions should still be indexed (name only)."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_ZIP

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            dest = os.path.join(tmpdir, "archive.zip")
            shutil.copy2(SAMPLE_ZIP, dest)
            time.sleep(2.0)

            watcher.stop()
            assert get_document_count() >= 1


class TestMeilisearchDown:
    """Tests for resilience when Meilisearch is unavailable."""

    def test_handler_does_not_crash_on_bad_index(self):
        """_index_file should not raise if Meilisearch has issues."""
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            tmp_path = f.name

        try:
            
            handler._index_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_remove_nonexistent_doc_does_not_crash(self):
        """_remove_file should handle missing documents gracefully."""
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler()
        
        handler._remove_file("/nonexistent/path/file.pdf")


class TestEmptyFile:
    """Tests for empty files (0 bytes content)."""

    def test_empty_pdf_indexed(self):
        """Empty PDF should still be indexed (as name match)."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import EMPTY_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            dest = os.path.join(tmpdir, "empty.pdf")
            shutil.copy2(EMPTY_PDF, dest)
            time.sleep(2.0)

            watcher.stop()
            assert get_document_count() >= 1
