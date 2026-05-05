from typing import Optional

from pydantic import BaseModel, Field


# ── Search Request (query params) ──────────────────────────

class SearchParams(BaseModel):
    q: str = Field("", max_length=500)
    file_type: Optional[str] = None
    department: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(None, pattern="^(asc|desc)$")


# ── Search Result Items ────────────────────────────────────

class ResultItem(BaseModel):
    id: str
    file_name: str
    department: str
    file_type: str
    file_size: int
    created_at: str
    modified_at: str
    highlight: str


class SearchResponse(BaseModel):
    query: str
    total_hits: int
    limit: int
    offset: int
    results: list[ResultItem]


# ── Document Metadata ──────────────────────────────────────

class DocumentDetail(BaseModel):
    id: str
    file_name: str
    file_path: str
    department: str
    file_type: str
    file_size: int
    created_at: str
    modified_at: str
    restricted: bool
