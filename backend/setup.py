"""
First-time setup script for BSI Search Engine.
Creates DB tables and a default admin user.

Usage:
    cd backend
    python setup.py
"""
import sys
from getpass import getpass

from database import engine, SessionLocal, Base
from models.user import User
from models.audit_log import AuditLog
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created.")


def create_admin_user(username=None, password=None):
    """Create the default admin user if it doesn't already exist."""
    username = username or DEFAULT_ADMIN_USERNAME
    password = password or DEFAULT_ADMIN_PASSWORD

    session = SessionLocal()
    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            print(f"[SKIP] User '{username}' already exists.")
            return False

        user = User(
            username=username,
            hashed_password=pwd_context.hash(password),
            full_name="Default Admin",
            role="admin",
            is_active=True,
        )
        session.add(user)
        session.commit()
        print(f"[OK] Admin user '{username}' created.")
        return True
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to create admin user: {e}")
        return False
    finally:
        session.close()


def verify_setup():
    """Verify that the setup completed successfully."""
    session = SessionLocal()
    try:
        admin_count = session.query(User).filter_by(role="admin", is_active=True).count()
        if admin_count > 0:
            print(f"[OK] Setup verified — {admin_count} admin user(s) found.")
            return True
        else:
            print("[WARN] No active admin users found.")
            return False
    finally:
        session.close()


def main():
    print("=" * 50)
    print("BSI Search Engine — First-Time Setup")
    print("=" * 50)

    # Step 1: Create tables
    create_tables()

    # Step 2: Create admin user
    create_admin_user()

    # Step 3: Verify
    verify_setup()

    print("\nSetup complete! You can now start the backend with:")
    print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
