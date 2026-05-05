import logging
import os
import threading
from pathlib import Path
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from config import DATA_FOLDER, SKIP_EXTENSIONS

logger = logging.getLogger(__name__)

# Default debounce window in seconds
DEBOUNCE_SECONDS = 1.5


class BSIFileHandler(FileSystemEventHandler):
    """Handles file system events in the BSI data folder.

    On created/modified: debounced index into Meilisearch.
    On deleted: immediate removal from Meilisearch (no debounce).
    """

    def __init__(self, data_root: Optional[str] = None, debounce_seconds: float = DEBOUNCE_SECONDS):
        super().__init__()
        self.data_root = data_root or DATA_FOLDER
        self.debounce_seconds = debounce_seconds
        self._events_log = []          
        self._pending = {}             
        self._pending_lock = threading.Lock()

    def _should_ignore(self, event: FileSystemEvent) -> bool:
        """Return True if this event should be ignored."""
        if event.is_directory:
            return True
        path = Path(event.src_path)
        name = path.name
        if name.startswith("~") or name.startswith("."):
            return True
        if name.endswith(".tmp") or name.endswith(".swp"):
            return True
        if path.suffix.lower() in SKIP_EXTENSIONS:
            return True
        return False

    def _index_file(self, file_path: str):
        """Build document from file and add/update in Meilisearch."""
        if not os.path.isfile(file_path):
            return

        from services.ingestion import build_document
        from services.meili_service import add_document

        try:
            doc = build_document(file_path, data_root=self.data_root)
            if doc is None:
                return
            add_document(doc)
            logger.info(f"[WATCHER] Indexed: {doc['file_name']} (id={doc['id']})")
        except Exception as e:
            logger.error(f"[WATCHER] Failed to index {file_path}: {e}")

    def _remove_file(self, file_path: str):
        """Remove document from Meilisearch by generating its ID."""
        from services.ingestion import generate_id
        from services.meili_service import remove_document

        doc_id = generate_id(file_path)
        try:
            remove_document(doc_id)
            logger.info(f"[WATCHER] Removed: {Path(file_path).name} (id={doc_id})")
        except Exception as e:
            logger.error(f"[WATCHER] Failed to remove {file_path}: {e}")

    def _schedule_index(self, file_path: str):
        """Debounce: cancel any pending timer for this file, schedule a new one."""
        with self._pending_lock:
            # Cancel existing timer if any
            old_timer = self._pending.get(file_path)
            if old_timer:
                old_timer.cancel()

            timer = threading.Timer(
                self.debounce_seconds,
                self._execute_index,
                args=[file_path],
            )
            timer.daemon = True
            self._pending[file_path] = timer
            timer.start()

    def _execute_index(self, file_path: str):
        """Called by the debounce timer — actually index the file."""
        with self._pending_lock:
            self._pending.pop(file_path, None)
        self._index_file(file_path)
        self._events_log.append(("indexed", file_path))

    def _cancel_pending(self, file_path: str):
        """Cancel any pending debounce timer for a file (used before delete)."""
        with self._pending_lock:
            timer = self._pending.pop(file_path, None)
            if timer:
                timer.cancel()

    def on_created(self, event: FileSystemEvent):
        if self._should_ignore(event):
            return
        file_path = event.src_path
        logger.info(f"[WATCHER] File created: {Path(file_path).name}")
        self._schedule_index(file_path)

    def on_modified(self, event: FileSystemEvent):
        if self._should_ignore(event):
            return
        file_path = event.src_path
        logger.info(f"[WATCHER] File modified: {Path(file_path).name}")
        self._schedule_index(file_path)

    def on_deleted(self, event: FileSystemEvent):
        if self._should_ignore(event):
            return
        file_path = event.src_path
        logger.info(f"[WATCHER] File deleted: {Path(file_path).name}")
        # Cancel any pending index for this file
        self._cancel_pending(file_path)
        self._remove_file(file_path)
        self._events_log.append(("deleted", file_path))

    def flush(self):
        """Wait for all pending debounce timers to fire. Useful for tests."""
        with self._pending_lock:
            timers = list(self._pending.values())
        for timer in timers:
            timer.join()

    def get_events(self):
        """Return list of processed events (for testing)."""
        return list(self._events_log)

    def clear_events(self):
        """Clear captured events and cancel pending timers."""
        with self._pending_lock:
            for timer in self._pending.values():
                timer.cancel()
            self._pending.clear()
        self._events_log.clear()

    @property
    def pending_count(self) -> int:
        """Number of files waiting for debounce to fire."""
        with self._pending_lock:
            return len(self._pending)


class BSIWatcher:
    """Manages a Watchdog observer for the BSI data folder.

    Usage:
        watcher = BSIWatcher()
        watcher.start()    # begins watching
        watcher.stop()     # stops watching
        watcher.status()   # returns current state
    """

    def __init__(self, watch_path: Optional[str] = None):
        self.watch_path = watch_path or DATA_FOLDER
        self.handler = BSIFileHandler(data_root=self.watch_path)
        self.observer = None
        self._running = False

    def start(self):
        """Start watching the data folder."""
        if self._running:
            logger.warning("[WATCHER] Already running")
            return

        path = Path(self.watch_path)
        if not path.exists():
            logger.error(f"[WATCHER] Watch path does not exist: {self.watch_path}")
            return

        self.observer = Observer()
        self.observer.schedule(self.handler, str(path), recursive=True)
        self.observer.daemon = True
        self.observer.start()
        self._running = True
        logger.info(f"[WATCHER] Started watching: {self.watch_path}")

    def stop(self):
        """Stop watching the data folder."""
        if not self._running:
            return

        self.handler.clear_events()
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None
        self._running = False
        logger.info("[WATCHER] Stopped")

    def status(self) -> dict:
        """Return watcher status."""
        return {
            "running": self._running,
            "watch_path": self.watch_path,
            "pending_index": self.handler.pending_count,
        }

    @property
    def is_running(self) -> bool:
        return self._running
