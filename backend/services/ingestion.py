import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import DATA_FOLDER, SKIP_EXTENSIONS

logger = logging.getLogger(__name__)


def generate_id(file_path: str) -> str:
    """Create a unique 12-char hex ID from file path hash."""
    return hashlib.md5(file_path.encode()).hexdigest()[:12]


def extract_department(file_path: str, data_root: str = None) -> str:
    """Get department from first subfolder after data root."""
    data_root = data_root or DATA_FOLDER
    rel_path = os.path.relpath(file_path, data_root)
    department = rel_path.split(os.sep)[0]
    return department


def get_file_metadata(file_path: str) -> dict:
    """Get file size and timestamps."""
    stat = os.stat(file_path)
    return {
        "file_size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
    }


def build_document(file_path: str, data_root: str = None) -> Optional[dict]:
    """Build a document dict from a file using filename + metadata only.

    Returns None if the file should be skipped (.lnk).
    """
    ext = Path(file_path).suffix.lower()

    
    if ext in SKIP_EXTENSIONS:
        return None

    # Build document from filename + metadata only
    metadata = get_file_metadata(file_path)
    doc = {
        "id": generate_id(file_path),
        "file_name": Path(file_path).name,
        "file_path": str(file_path),
        "file_type": ext.lstrip("."),
        "department": extract_department(file_path, data_root),
        "file_size": metadata["file_size"],
        "created_at": metadata["created_at"],
        "modified_at": metadata["modified_at"],
        "restricted": False,
    }

    return doc


def scan_directory(data_root: str = None) -> list[dict]:
    """Scan a directory and build documents for all files.

    Returns a list of document dicts ready for Meilisearch.
    """
    data_root = data_root or DATA_FOLDER
    documents = []
    errors = []

    for root, dirs, files in os.walk(data_root):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                doc = build_document(file_path, data_root)
                if doc is not None:
                    documents.append(doc)
            except Exception as e:
                errors.append((file_path, str(e)))
                logger.error(f"Ingestion failed for {file_path}: {e}")

    if errors:
        logger.warning(f"Ingestion completed with {len(errors)} errors out of {len(documents) + len(errors)} files")
    else:
        logger.info(f"Ingestion completed: {len(documents)} files indexed")

    return documents
