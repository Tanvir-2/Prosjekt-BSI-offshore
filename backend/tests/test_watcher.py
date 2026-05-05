import pytest
import time
import os
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


class TestBSIFileHandlerIgnoreRules:
    """Tests for event filtering (no Meilisearch needed)."""

    def test_ignores_directory_events(self):
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler()

        class FakeEvent:
            is_directory = True
            src_path = "/data/Prosjekt/new_folder"

        handler.on_created(FakeEvent())
        assert len(handler.get_events()) == 0

    def test_ignores_temp_files(self):
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler()

        for name in ["~report.docx", ".hidden", "file.tmp", "file.swp"]:
            class FakeEvent:
                is_directory = False
                src_path = f"/data/Prosjekt/{name}"
            handler.on_created(FakeEvent())

        assert len(handler.get_events()) == 0

    def test_ignores_lnk_files(self):
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler()

        class FakeEvent:
            is_directory = False
            src_path = "/data/Prosjekt/shortcut.lnk"

        handler.on_created(FakeEvent())
        assert len(handler.get_events()) == 0

    def test_accepts_valid_extensions(self):
        """Verify _should_ignore accepts valid extensions."""
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler()

        for ext in [".pdf", ".docx", ".xlsx", ".pptx", ".msg", ".png"]:
            class FakeEvent:
                is_directory = False
                src_path = f"/data/Prosjekt/file{ext}"
            assert handler._should_ignore(FakeEvent()) is False


class TestDebounce:
    """Tests for debouncing created/modified events."""

    def test_rapid_creates_produce_single_index(self):
        """Multiple created events for same file should result in one index."""
        from services.watcher import BSIFileHandler

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test content")
            tmp_path = f.name

        try:
            handler = BSIFileHandler(debounce_seconds=0.3)

            class FakeEvent:
                is_directory = False
                src_path = tmp_path

            
            for _ in range(5):
                handler.on_created(FakeEvent())

            
            assert handler.pending_count == 1  
            assert len(handler.get_events()) == 0

            
            handler.flush()
            assert len(handler.get_events()) == 1  
            assert handler.get_events()[0][0] == "indexed"
        finally:
            handler.clear_events()
            os.unlink(tmp_path)

    def test_modified_after_create_resets_timer(self):
        """Modified event right after create should reset the debounce timer."""
        from services.watcher import BSIFileHandler

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            tmp_path = f.name

        try:
            handler = BSIFileHandler(debounce_seconds=0.3)

            class FakeEvent:
                is_directory = False
                src_path = tmp_path

            handler.on_created(FakeEvent())
            time.sleep(0.15) 
            handler.on_modified(FakeEvent())  

           
            time.sleep(0.2)
            assert len(handler.get_events()) == 0

            
            handler.flush()
            assert len(handler.get_events()) == 1
        finally:
            handler.clear_events()
            os.unlink(tmp_path)

    def test_delete_executes_immediately(self):
        """Delete events should NOT be debounced — execute immediately."""
        from services.watcher import BSIFileHandler
        handler = BSIFileHandler(debounce_seconds=5.0)  

        class FakeEvent:
            is_directory = False
            src_path = "/data/test.pdf"

        handler.on_deleted(FakeEvent())
        
        assert len(handler.get_events()) == 1
        assert handler.get_events()[0][0] == "deleted"
        handler.clear_events()

    def test_delete_cancels_pending_index(self):
        """Deleting a file should cancel any pending index timer."""
        from services.watcher import BSIFileHandler

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            tmp_path = f.name

        try:
            handler = BSIFileHandler(debounce_seconds=2.0)

            class FakeEvent:
                is_directory = False
                src_path = tmp_path

            handler.on_created(FakeEvent())
            assert handler.pending_count == 1

            
            handler._cancel_pending(tmp_path)
            assert handler.pending_count == 0
        finally:
            handler.clear_events()
            os.unlink(tmp_path)

    def test_different_files_debounced_independently(self):
        """Two different files should have independent debounce timers."""
        from services.watcher import BSIFileHandler

        files = []
        for i in range(2):
            f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            f.write(b"%PDF-1.4 test")
            f.close()
            files.append(f.name)

        try:
            handler = BSIFileHandler(debounce_seconds=0.3)

            for path in files:
                class FakeEvent:
                    is_directory = False
                    src_path = path
                handler.on_created(FakeEvent())

            assert handler.pending_count == 2
            handler.flush()
            assert len(handler.get_events()) == 2
        finally:
            handler.clear_events()
            for path in files:
                os.unlink(path)

    def test_clear_events_cancels_timers(self):
        """clear_events should cancel all pending debounce timers."""
        from services.watcher import BSIFileHandler

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            tmp_path = f.name

        try:
            handler = BSIFileHandler(debounce_seconds=5.0)

            class FakeEvent:
                is_directory = False
                src_path = tmp_path

            handler.on_created(FakeEvent())
            assert handler.pending_count == 1

            handler.clear_events()
            assert handler.pending_count == 0
            assert len(handler.get_events()) == 0
        finally:
            os.unlink(tmp_path)


class TestWatcherIndexingIntegration:
    """Integration tests: real files, real Meilisearch, debounced."""

    def test_new_pdf_is_searchable(self):
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            import shutil
            dest = os.path.join(tmpdir, "test_report.pdf")
            shutil.copy2(SAMPLE_PDF, dest)

            
            time.sleep(2.0)

            watcher.stop()
            assert get_document_count() >= 1

    def test_deleted_file_removed_from_index(self):
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            import shutil
            dest = os.path.join(tmpdir, "to_delete.pdf")
            shutil.copy2(SAMPLE_PDF, dest)

            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            time.sleep(0.3)

            
            watcher.handler.flush()
            time.sleep(0.3)
            count_before = get_document_count()
            assert count_before >= 1

            os.remove(dest)
            time.sleep(0.5)

            count_after = get_document_count()
            watcher.stop()
            assert count_after < count_before

    def test_rapid_copies_produce_single_index(self):
        """Copying same file multiple times should only index once (debounced)."""
        from services.watcher import BSIWatcher
        from services.meili_service import get_document_count
        from tests.fixtures import SAMPLE_PDF

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            
            watcher.handler.debounce_seconds = 0.5
            watcher.start()
            time.sleep(0.3)

            import shutil
            dest = os.path.join(tmpdir, "report.pdf")

            
            for _ in range(5):
                shutil.copy2(SAMPLE_PDF, dest)
                time.sleep(0.1)

            
            watcher.handler.flush()
            time.sleep(0.3)

            count = get_document_count()
            watcher.stop()
            
            assert count == 1


class TestBSIWatcherLifecycle:
    """Tests for watcher start/stop/status."""

    def test_status_before_start(self):
        from services.watcher import BSIWatcher
        watcher = BSIWatcher()
        status = watcher.status()
        assert status["running"] is False

    def test_not_running_initially(self):
        from services.watcher import BSIWatcher
        watcher = BSIWatcher()
        assert watcher.is_running is False

    def test_start_and_stop(self):
        from services.watcher import BSIWatcher
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            assert watcher.is_running is True
            watcher.stop()
            assert watcher.is_running is False

    def test_double_start_safe(self):
        from services.watcher import BSIWatcher
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = BSIWatcher(watch_path=tmpdir)
            watcher.start()
            watcher.start()
            assert watcher.is_running is True
            watcher.stop()

    def test_stop_without_start_safe(self):
        from services.watcher import BSIWatcher
        watcher = BSIWatcher()
        watcher.stop()
        assert watcher.is_running is False

    def test_nonexistent_watch_path(self):
        from services.watcher import BSIWatcher
        watcher = BSIWatcher(watch_path="/nonexistent/path/abc123")
        watcher.start()
        assert watcher.is_running is False
