import pytest
from datetime import datetime
from sqlalchemy import inspect


class TestUserModel:
    """Tests for the User model."""

    def test_user_table_exists(self):
        """User table should be created in the database."""
        from database import engine
        assert "users" in inspect(engine).get_table_names()

    def test_user_columns(self):
        """User table should have all required columns."""
        from database import engine
        columns = {col["name"] for col in inspect(engine).get_columns("users")}
        expected = {
            "id", "username", "hashed_password", "full_name",
            "role", "is_active", "created_at", "updated_at"
        }
        assert columns == expected

    def test_username_is_unique(self):
        """Username column should have a unique constraint or unique index."""
        from database import engine
        from sqlalchemy import text
        # Ensure table exists (isolated_db may have dropped it)
        with engine.connect() as conn:
            # Use raw SQLite pragma to check unique columns — most reliable
            result = conn.execute(text("PRAGMA index_list('users')")).fetchall()
            unique_index_names = [row[1] for row in result if row[2]]  # row[2] = unique flag
            for idx_name in unique_index_names:
                cols = conn.execute(text(f"PRAGMA index_info('{idx_name}')")).fetchall()
                col_names = [col[2] for col in cols]
                if col_names == ["username"]:
                    return  # found unique index on username
        # Fallback: check SQLAlchemy reflection
        insp = inspect(engine)
        uniques = [
            col["column_names"]
            for col in insp.get_unique_constraints("users")
        ]
        unique_indexes = [
            idx["column_names"]
            for idx in insp.get_indexes("users")
            if idx["unique"]
        ]
        assert ["username"] in uniques or ["username"] in unique_indexes

    def test_create_and_query_user(self, db_session):
        """Should be able to insert and retrieve a user."""
        from models.user import User
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            username="admin",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        fetched = db_session.query(User).filter_by(username="admin").first()
        assert fetched is not None
        assert fetched.username == "admin"
        assert fetched.role == "admin"
        assert fetched.is_active is True
        assert fetched.full_name == "Admin User"
        assert pwd_context.verify("admin123", fetched.hashed_password)

    def test_username_unique_constraint_enforced(self, db_session):
        """Duplicate username should raise an error."""
        from models.user import User
        from sqlalchemy.exc import IntegrityError

        db_session.add(User(username="testuser", hashed_password="hash", role="hr"))
        db_session.commit()

        db_session.add(User(username="testuser", hashed_password="hash2", role="hr"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_role_defaults_to_hr(self, db_session):
        """If no role specified, it should default to 'hr'."""
        from models.user import User

        user = User(username="defaultrole", hashed_password="hash")
        db_session.add(user)
        db_session.commit()

        fetched = db_session.query(User).filter_by(username="defaultrole").first()
        assert fetched.role == "hr"

    def test_is_active_defaults_true(self, db_session):
        """New users should be active by default."""
        from models.user import User

        user = User(username="activeuser", hashed_password="hash")
        db_session.add(user)
        db_session.commit()

        fetched = db_session.query(User).filter_by(username="activeuser").first()
        assert fetched.is_active is True

    def test_created_at_auto_set(self, db_session):
        """created_at should be automatically set on insert."""
        from models.user import User

        user = User(username="dateuser", hashed_password="hash")
        db_session.add(user)
        db_session.commit()

        fetched = db_session.query(User).filter_by(username="dateuser").first()
        assert fetched.created_at is not None
        assert isinstance(fetched.created_at, datetime)


class TestAuditLogModel:
    """Tests for the AuditLog model."""

    def test_audit_log_table_exists(self):
        """audit_logs table should be created."""
        from database import engine
        assert "audit_logs" in inspect(engine).get_table_names()

    def test_audit_log_columns(self):
        """audit_logs table should have all required columns."""
        from database import engine
        columns = {col["name"] for col in inspect(engine).get_columns("audit_logs")}
        expected = {"id", "user_id", "action", "details", "timestamp"}
        assert columns == expected

    def test_create_audit_log(self, db_session, admin_user):
        """Should be able to create an audit log linked to a user."""
        from models.audit_log import AuditLog

        log = AuditLog(
            user_id=admin_user.id,
            action="login",
            details="User logged in from 127.0.0.1",
        )
        db_session.add(log)
        db_session.commit()

        fetched = db_session.query(AuditLog).first()
        assert fetched is not None
        assert fetched.action == "login"
        assert fetched.user_id == admin_user.id
        assert fetched.details == "User logged in from 127.0.0.1"
        assert fetched.timestamp is not None

    def test_audit_log_user_relationship(self, db_session, hr_user):
        """AuditLog should have access to the related User object."""
        from models.audit_log import AuditLog

        log = AuditLog(user_id=hr_user.id, action="search")
        db_session.add(log)
        db_session.commit()

        fetched = db_session.query(AuditLog).first()
        assert fetched.user.username == "hruser"

    def test_user_audit_logs_relationship(self, db_session, hr_user):
        """User should have access to their audit logs."""
        from models.audit_log import AuditLog

        db_session.add(AuditLog(user_id=hr_user.id, action="login"))
        db_session.add(AuditLog(user_id=hr_user.id, action="search"))
        db_session.commit()

        db_session.refresh(hr_user)
        assert len(hr_user.audit_logs) == 2
        assert {log.action for log in hr_user.audit_logs} == {"login", "search"}

    def test_audit_log_user_id_foreign_key(self):
        """user_id should reference the users table."""
        from database import engine
        fks = inspect(engine).get_foreign_keys("audit_logs")
        assert len(fks) == 1
        assert fks[0]["constrained_columns"] == ["user_id"]
        assert fks[0]["referred_table"] == "users"
