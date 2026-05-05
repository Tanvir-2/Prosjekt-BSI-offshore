import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from models.user import User
from routers.auth import get_current_user
from schemas.search import DocumentDetail
from services.meili_service import get_document, get_department_filter
from config import DATA_FOLDER

router = APIRouter(prefix="/api/docs", tags=["documents"])


def _check_access(user: User, department: str):
    """Verify user has access to the given department."""
    role_filter = get_department_filter(user.role)
    
    if role_filter is None:
        return
    
    from config import ROLE_DEPARTMENT_ACCESS
    allowed = ROLE_DEPARTMENT_ACCESS.get(user.role, [])
    if department not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this department",
        )


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_doc_metadata(
    doc_id: str,
    user: User = Depends(get_current_user),
):
    """Get file metadata by document ID."""
    try:
        doc = get_document(doc_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    _check_access(user, doc.get("department", ""))
    return doc


@router.get("/{doc_id}/preview")
def preview_file(
    doc_id: str,
    user: User = Depends(get_current_user),
):
    """Stream file for in-browser preview."""
    try:
        doc = get_document(doc_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    _check_access(user, doc.get("department", ""))

    file_path = doc.get("file_path", "")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        file_path,
        media_type=_get_media_type(file_path),
        filename=doc.get("file_name", Path(file_path).name),
        content_disposition_type="inline",
    )


@router.get("/{doc_id}/download")
def download_file(
    doc_id: str,
    user: User = Depends(get_current_user),
):
    """Download file as attachment."""
    try:
        doc = get_document(doc_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    _check_access(user, doc.get("department", ""))

    file_path = doc.get("file_path", "")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=doc.get("file_name", Path(file_path).name),
        content_disposition_type="attachment",
    )


def _get_media_type(file_path: str) -> str:
    """Return MIME type based on file extension."""
    ext = Path(file_path).suffix.lower()
    types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsm": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".doc": "application/msword",
        ".dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
        ".msg": "application/vnd.ms-outlook",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".heic": "image/heic",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".zip": "application/zip",
    }
    return types.get(ext, "application/octet-stream")
