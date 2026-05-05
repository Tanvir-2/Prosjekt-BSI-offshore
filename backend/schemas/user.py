from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from config import VALID_ROLES


# ── Auth ────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: Optional[str] = None
    username: str


# ── User CRUD ───────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(None, max_length=100)
    role: str = Field("hr", pattern=f"^({'|'.join(VALID_ROLES)})$")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, pattern=f"^({'|'.join(VALID_ROLES)})$")
    is_active: Optional[bool] = None




class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)




class ConfigResponse(BaseModel):
    data_folder: str


class ConfigUpdate(BaseModel):
    data_folder: str = Field(..., min_length=1)




class StatsResponse(BaseModel):
    total_documents: int
    by_department: dict[str, int]
    by_file_type: dict[str, int]
