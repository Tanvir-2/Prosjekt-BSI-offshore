import pytest
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from database import engine, SessionLocal, Base
from models.user import User
from models.audit_log import AuditLog


@pytest.fixture(autouse=True)
def isolated_db():
    """Ensure every test starts with a clean database.
    Drops all tables, recreates them, then drops after test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a transactional DB session that rolls back after each test."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def fast_client():
    """TestClient that skips Meilisearch setup, bulk indexing, and file watcher.
    Use for auth, admin, and other tests that don't need search."""

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    from config import FRONTEND_URL
    from fastapi.middleware.cors import CORSMiddleware
    from routers.auth import router as auth_router
    from routers.search import router as search_router
    from routers.documents import router as docs_router
    from routers.admin import router as admin_router

    app = FastAPI(lifespan=_noop_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(search_router)
    app.include_router(docs_router)
    app.include_router(admin_router)

    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_user(db_session):
    """Create and return a default admin user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        username="admin",
        hashed_password=pwd_context.hash("admin123"),
        full_name="Test Admin",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def hr_user(db_session):
    """Create and return an HR user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        username="hruser",
        hashed_password=pwd_context.hash("hrpass"),
        full_name="Test HR",
        role="hr",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def pm_user(db_session):
    """Create and return a project manager user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        username="pmuser",
        hashed_password=pwd_context.hash("pmpass"),
        full_name="Test PM",
        role="project_manager",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
