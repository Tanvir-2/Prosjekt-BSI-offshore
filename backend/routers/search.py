from typing import Optional

from fastapi import APIRouter, Depends, Query

from models.user import User
from routers.auth import get_current_user
from schemas.search import SearchResponse
from services.meili_service import (
    search_documents,
    format_search_response,
    get_department_filter,
)

router = APIRouter(prefix="/api/search", tags=["search"])


def _build_filters(
    department: Optional[str],
    file_type: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    role_filter: Optional[list],
) -> list:
    """Combine all filter conditions into a Meilisearch filter list."""
    filters = []

    # Role-based department filter
    if role_filter:
        filters.extend(role_filter)

    if department:
        filters.append(f"department = {department}")
    if file_type:
        filters.append(f"file_type = {file_type}")
    if date_from:
        filters.append(f"created_at >= {date_from}")
    if date_to:
        filters.append(f"created_at <= {date_to}")

    return filters if filters else None


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query("", max_length=500),
    file_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Search documents with query, filters, pagination, and role-based access."""
    # Get role-based department filter
    role_filter = get_department_filter(user.role)

    # Build combined filters
    filters = _build_filters(
        department=department,
        file_type=file_type,
        date_from=date_from,
        date_to=date_to,
        role_filter=role_filter,
    )

   
    sort = None
    if sort_by and sort_order:
        sort = [f"{sort_by}:{sort_order}"]

    
    raw = search_documents(
        query=q,
        filters=filters,
        limit=limit,
        offset=offset,
        sort=sort,
    )

    return format_search_response(raw, query=q)


@router.get("/suggest", response_model=SearchResponse)
def suggest(
    q: str = Query("", max_length=500),
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
):
    """Quick search-as-you-type endpoint with fewer results."""
    role_filter = get_department_filter(user.role)

    raw = search_documents(
        query=q,
        filters=role_filter,
        limit=limit,
        offset=0,
    )

    return format_search_response(raw, query=q)
