import pytest
from sqlalchemy import inspect


class TestCreateTables:
    """Tests for the create_tables function."""

    def test_creates_users_table(self):
        from setup import create_tables
        from database import engine
        create_tables()
        assert "users" in inspect(engine).get_table_names()

    def test_creates_audit_logs_table(self):
        from setup import create_tables
        from database import engine
        create_tables()
        assert "audit_logs" in inspect(engine).get_table_names()

    def test_idempotent(self):
        """Calling create_tables twice should not error."""
        from setup import create_tables
        from database import engine
        create_tables()
        create_tables()
        assert "users" in inspect(engine).get_table_names()


class TestCreateAdminUser:
    """Tests for the create_admin_user function."""

    def test_creates_admin_with_defaults(self, db_session):
        from setup import create_admin_user
        from models.user import User
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        result = create_admin_user()
        assert result is True

        admin = db_session.query(User).filter_by(username="admin").first()
        assert admin is not None
        assert admin.role == "admin"
        assert admin.is_active is True
        assert admin.full_name == "Default Admin"
        assert pwd_context.verify("admin123", admin.hashed_password)

    def test_creates_admin_with_custom_credentials(self, db_session):
        from setup import create_admin_user
        from models.user import User
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        result = create_admin_user(username="customadmin", password="custompass")
        assert result is True

        admin = db_session.query(User).filter_by(username="customadmin").first()
        assert admin is not None
        assert pwd_context.verify("custompass", admin.hashed_password)

    def test_skips_if_user_already_exists(self):
        from setup import create_admin_user
        assert create_admin_user() is True
        assert create_admin_user() is False

    def test_password_is_bcrypt_hashed(self, db_session):
        from setup import create_admin_user
        from models.user import User

        create_admin_user()
        admin = db_session.query(User).filter_by(username="admin").first()
        assert admin.hashed_password.startswith("$2b$")
        assert admin.hashed_password != "admin123"


class TestVerifySetup:
    """Tests for the verify_setup function."""

    def test_verify_fails_without_admin(self):
        from setup import verify_setup
        assert verify_setup() is False

    def test_verify_passes_after_admin_creation(self):
        from setup import create_admin_user, verify_setup
        create_admin_user()
        assert verify_setup() is True

    def test_verify_fails_if_admin_deactivated(self, db_session):
        from setup import create_admin_user, verify_setup
        from models.user import User

        create_admin_user()
        admin = db_session.query(User).filter_by(username="admin").first()
        admin.is_active = False
        db_session.commit()

        assert verify_setup() is False
