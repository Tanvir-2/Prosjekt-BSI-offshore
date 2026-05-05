import pytest

from services.auth import create_token


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def admin_token(admin_user):
    """Return a valid JWT for the admin user."""
    return create_token({
        "sub": admin_user.username,
        "role": admin_user.role,
        "full_name": admin_user.full_name or "",
    })


@pytest.fixture
def hr_token(hr_user):
    """Return a valid JWT for the HR user."""
    return create_token({
        "sub": hr_user.username,
        "role": hr_user.role,
        "full_name": hr_user.full_name or "",
    })


@pytest.fixture
def pm_token(pm_user):
    """Return a valid JWT for the project manager user."""
    return create_token({
        "sub": pm_user.username,
        "role": pm_user.role,
        "full_name": pm_user.full_name or "",
    })




class TestLogin:
    def test_login_success(self, fast_client, admin_user):
        resp = fast_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "admin"
        assert data["username"] == "admin"

    def test_login_wrong_password(self, fast_client, admin_user):
        resp = fast_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrongpass",
        })
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_login_nonexistent_user(self, fast_client):
        resp = fast_client.post("/api/auth/login", json={
            "username": "ghost",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_login_deactivated_user(self, fast_client, db_session, admin_user):
        admin_user.is_active = False
        db_session.commit()
        resp = fast_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        assert resp.status_code == 401
        assert "deactivated" in resp.json()["detail"].lower()

    def test_login_hr_user(self, fast_client, hr_user):
        resp = fast_client.post("/api/auth/login", json={
            "username": "hruser",
            "password": "hrpass",
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "hr"

    def test_login_pm_user(self, fast_client, pm_user):
        resp = fast_client.post("/api/auth/login", json={
            "username": "pmuser",
            "password": "pmpass",
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "project_manager"

    def test_login_missing_fields(self, fast_client):
        resp = fast_client.post("/api/auth/login", json={})
        assert resp.status_code == 422  # Validation error




class TestLogout:
    def test_logout_success(self, fast_client, admin_token):
        resp = fast_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "logged out" in resp.json()["message"].lower()

    def test_logout_no_token(self, fast_client):
        resp = fast_client.post("/api/auth/logout")
        assert resp.status_code == 200  # logout is stateless




class TestGetMe:
    def test_me_success(self, fast_client, admin_token):
        resp = fast_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert "hashed_password" not in data

    def test_me_hr_user(self, fast_client, hr_token):
        resp = fast_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "hr"

    def test_me_no_token(self, fast_client):
        resp = fast_client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, fast_client):
        resp = fast_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_me_token_via_query_param(self, fast_client, admin_token):
        resp = fast_client.get(f"/api/auth/me?token={admin_token}")
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"

    def test_me_returns_user_fields(self, fast_client, admin_token):
        resp = fast_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = resp.json()
        assert "id" in data
        assert "username" in data
        assert "full_name" in data
        assert "role" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data




class TestRequireRole:
    def test_admin_role_check(self, fast_client, admin_token):
        """Admin token should have admin role."""
        resp = fast_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_hr_role_check(self, fast_client, hr_token):
        """HR token should have hr role."""
        resp = fast_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "hr"
