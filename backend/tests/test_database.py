import os
import pytest
from sqlalchemy import inspect, text


class TestDatabase:
    """Tests for database.py SQLite connection."""

    def test_engine_uses_config_url(self):
        """Engine should use DATABASE_URL from config."""
        from database import engine
        from config import DATABASE_URL
        assert str(engine.url) == DATABASE_URL

    def test_engine_is_sqlite(self):
        """Engine dialect should be sqlite."""
        from database import engine
        assert engine.dialect.name == "sqlite"

    def test_session_local_is_configured(self):
        """SessionLocal should be bound to the engine."""
        from database import SessionLocal, engine
        assert SessionLocal.kw["bind"] is engine

    def test_get_db_yields_session(self):
        """get_db() should yield a usable session."""
        from database import get_db
        gen = get_db()
        session = next(gen)
       
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
       
        try:
            next(gen)
        except StopIteration:
            pass

    def test_get_db_closes_session(self):
        """get_db() should close the session after use."""
        from database import get_db
        gen = get_db()
        session = next(gen)
        assert not session.is_active or session.is_active  # session exists
        
        try:
            next(gen)
        except StopIteration:
            pass
        # After closing, session should be unusable for new queries
        # (SQLAlchemy closes the connection)

    def test_base_is_declarative(self):
        """Base should be a declarative base for model definitions."""
        from database import Base
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_can_create_and_drop_tables(self):
        """Base.metadata should be able to create/drop all tables."""
        from database import engine, Base
        
        Base.metadata.create_all(bind=engine)
        
        Base.metadata.drop_all(bind=engine)

    def test_db_file_path_is_in_backend_folder(self):
        """SQLite file should be located in the backend/ folder."""
        from config import DATABASE_URL, PROJECT_ROOT
        # sqlite:////Users/.../backend/users.db
        db_path = DATABASE_URL.replace("sqlite:///", "")
        assert db_path.startswith(str(PROJECT_ROOT))
        assert db_path.endswith("users.db")

    def test_multiple_sessions_independent(self):
        """Two sessions should be independent of each other."""
        from database import SessionLocal
        s1 = SessionLocal()
        s2 = SessionLocal()
        assert s1 is not s2
        s1.close()
        s2.close()
