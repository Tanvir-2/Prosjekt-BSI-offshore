import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config import DATA_FOLDER, PROJECT_ROOT, VALID_ROLES
from database import get_db
from models.user import User
from routers.auth import get_current_user, require_role
from schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    ConfigResponse, ConfigUpdate, StatsResponse,
)
from services.auth import hash_password
from services.meili_service import (
    get_document_count, bulk_index, get_index,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── User Management ───────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def list_users(
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all users. Admin only."""
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new user. Admin only."""
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' already exists",
        )

    new_user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    body: UserUpdate,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Update a user's role, name, or active status. Admin only."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.full_name is not None:
        target.full_name = body.full_name
    if body.role is not None:
        target.role = body.role
    if body.is_active is not None:
        target.is_active = body.is_active

    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: int,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Deactivate a user (soft delete). Admin only."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    target.is_active = False
    db.commit()
    return {"message": f"User '{target.username}' deactivated"}


@router.delete("/users/{user_id}/delete")
def hard_delete_user(
    user_id: int,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Permanently delete a user from the database. Admin only."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    db.delete(target)
    db.commit()
    return {"message": f"User '{target.username}' permanently deleted"}


# ── Config ────────────────────────────────────────────────

@router.get("/config", response_model=ConfigResponse)
def get_config(user: User = Depends(require_role("admin"))):
    """Get current data folder path. Admin only."""
    return ConfigResponse(data_folder=DATA_FOLDER)


@router.put("/config", response_model=ConfigResponse)
def update_config(
    body: ConfigUpdate,
    user: User = Depends(require_role("admin")),
):
    """Update data folder path in .env file. Admin only."""
    new_path = Path(body.data_folder)
    if not new_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path does not exist: {body.data_folder}",
        )

    env_path = PROJECT_ROOT / ".env"
    _update_env_var(env_path, "DATA_FOLDER", body.data_folder)
    return ConfigResponse(data_folder=body.data_folder)


def _update_env_var(env_path: Path, key: str, value: str):
    """Update a single variable in the .env file."""
    lines = []
    found = False
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)




@router.post("/reindex")
def reindex(user: User = Depends(require_role("admin"))):
    """Trigger full re-scan and re-index of the data folder. Admin only."""
    from services.meili_service import delete_index, setup_index
    delete_index()
    setup_index()
    total = bulk_index(DATA_FOLDER)
    return {"message": f"Re-indexed {total} documents"}




@router.get("/stats", response_model=StatsResponse)
def get_stats(user: User = Depends(require_role("admin"))):
    """Get indexing statistics. Admin only."""
    index = get_index()
    stats = index.get_stats()
    total = stats.number_of_documents

    
    by_department = {}
    by_file_type = {}

    if total > 0:
       
        result = index.search("", {
            "limit": 0,
            "facets": ["department", "file_type"],
        })
        facet_dist = result.get("facetDistribution", {})
        by_department = facet_dist.get("department", {})
        by_file_type = facet_dist.get("file_type", {})

    return StatsResponse(
        total_documents=total,
        by_department=by_department,
        by_file_type=by_file_type,
    )
