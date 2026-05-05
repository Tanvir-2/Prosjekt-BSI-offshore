import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.auth import create_token


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def admin_token(admin_user):
    return create_token({"sub": admin_user.username, "role": admin_user.role, "full_name": ""})


@pytest.fixture
def hr_token(hr_user):
    return create_token({"sub": hr_user.username, "role": hr_user.role, "full_name": ""})


@pytest.fixture
def pm_token(pm_user):
    return create_token({"sub": pm_user.username, "role": pm_user.role, "full_name": ""})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Admin-only access ────────────────────────────────────

class TestAdminOnly:
    def test_hr_cannot_access_admin(self, fast_client, hr_token):
        for endpoint in [
            "/api/admin/users",
            "/api/admin/config",
            "/api/admin/stats",
        ]:
            resp = fast_client.get(endpoint, headers=auth_header(hr_token))
            assert resp.status_code == 403, f"{endpoint} should be 403 for HR"

    def test_pm_cannot_access_admin(self, fast_client, pm_token):
        resp = fast_client.get("/api/admin/users", headers=auth_header(pm_token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access(self, fast_client):
        resp = fast_client.get("/api/admin/users")
        assert resp.status_code == 401




class TestListUsers:
    def test_list_users(self, fast_client, admin_token, admin_user):
        resp = fast_client.get("/api/admin/users", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["username"] == "admin"

    def test_list_users_no_password(self, fast_client, admin_token):
        resp = fast_client.get("/api/admin/users", headers=auth_header(admin_token))
        for user in resp.json():
            assert "hashed_password" not in user
            assert "password" not in user




class TestCreateUser:
    def test_create_user(self, fast_client, admin_token):
        resp = fast_client.post("/api/admin/users", headers=auth_header(admin_token), json={
            "username": "newuser",
            "password": "secure123",
            "full_name": "New User",
            "role": "hr",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["role"] == "hr"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_duplicate_user_fails(self, fast_client, admin_token, admin_user):
        resp = fast_client.post("/api/admin/users", headers=auth_header(admin_token), json={
            "username": "admin",
            "password": "test123456",
            "role": "admin",
        })
        assert resp.status_code == 409

    def test_create_user_invalid_role(self, fast_client, admin_token):
        resp = fast_client.post("/api/admin/users", headers=auth_header(admin_token), json={
            "username": "hacker",
            "password": "test123456",
            "role": "superadmin",
        })
        assert resp.status_code == 422

    def test_create_user_short_username(self, fast_client, admin_token):
        resp = fast_client.post("/api/admin/users", headers=auth_header(admin_token), json={
            "username": "ab",
            "password": "test123456",
        })
        assert resp.status_code == 422

    def test_create_user_short_password(self, fast_client, admin_token):
        resp = fast_client.post("/api/admin/users", headers=auth_header(admin_token), json={
            "username": "goodname",
            "password": "abc",
        })
        assert resp.status_code == 422

    def test_created_user_can_login(self, fast_client, admin_token):
        
        fast_client.post("/api/admin/users", headers=auth_header(admin_token), json={
            "username": "loginuser",
            "password": "loginpass123",
            "role": "hr",
        })
        
        resp = fast_client.post("/api/auth/login", json={
            "username": "loginuser",
            "password": "loginpass123",
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "hr"




class TestUpdateUser:
    def test_update_role(self, fast_client, admin_token, hr_user):
        resp = fast_client.put(
            f"/api/admin/users/{hr_user.id}",
            headers=auth_header(admin_token),
            json={"role": "project_manager"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "project_manager"

    def test_update_full_name(self, fast_client, admin_token, hr_user):
        resp = fast_client.put(
            f"/api/admin/users/{hr_user.id}",
            headers=auth_header(admin_token),
            json={"full_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_deactivate_user(self, fast_client, admin_token, hr_user):
        resp = fast_client.put(
            f"/api/admin/users/{hr_user.id}",
            headers=auth_header(admin_token),
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_update_nonexistent_user(self, fast_client, admin_token):
        resp = fast_client.put(
            "/api/admin/users/9999",
            headers=auth_header(admin_token),
            json={"role": "hr"},
        )
        assert resp.status_code == 404

    def test_partial_update(self, fast_client, admin_token, hr_user):
        """Only send one field — the rest should stay unchanged."""
        resp = fast_client.put(
            f"/api/admin/users/{hr_user.id}",
            headers=auth_header(admin_token),
            json={"full_name": "Only Name Changed"},
        )
        data = resp.json()
        assert data["full_name"] == "Only Name Changed"
        assert data["role"] == "hr"  # unchanged
        assert data["is_active"] is True  # unchanged




class TestDeactivateUser:
    def test_deactivate_user(self, fast_client, admin_token, hr_user):
        resp = fast_client.delete(
            f"/api/admin/users/{hr_user.id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "deactivated" in resp.json()["message"].lower()

    def test_cannot_deactivate_self(self, fast_client, admin_token, admin_user):
        resp = fast_client.delete(
            f"/api/admin/users/{admin_user.id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400
        assert "own" in resp.json()["detail"].lower()

    def test_deactivate_nonexistent(self, fast_client, admin_token):
        resp = fast_client.delete(
            "/api/admin/users/9999",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    def test_deactivated_user_cannot_login(self, fast_client, admin_token, db_session, hr_user):
        fast_client.delete(f"/api/admin/users/{hr_user.id}", headers=auth_header(admin_token))
        resp = fast_client.post("/api/auth/login", json={
            "username": "hruser",
            "password": "hrpass",
        })
        assert resp.status_code == 401




class TestGetConfig:
    def test_get_config(self, fast_client, admin_token):
        resp = fast_client.get("/api/admin/config", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "data_folder" in resp.json()




class TestUpdateConfig:
    def test_update_config_valid_path(self, fast_client, admin_token):
        from config import PROJECT_ROOT
        # Save original .env content so we can restore it
        env_path = PROJECT_ROOT / ".env"
        original = env_path.read_text() if env_path.exists() else ""
        try:
            resp = fast_client.put("/api/admin/config", headers=auth_header(admin_token), json={
                "data_folder": str(PROJECT_ROOT),
            })
            assert resp.status_code == 200
            assert resp.json()["data_folder"] == str(PROJECT_ROOT)
        finally:
            # Restore original .env to avoid breaking other tests
            env_path.write_text(original)

    def test_update_config_invalid_path(self, fast_client, admin_token):
        resp = fast_client.put("/api/admin/config", headers=auth_header(admin_token), json={
            "data_folder": "/nonexistent/path/xyz",
        })
        assert resp.status_code == 400

    def test_update_config_empty_path(self, fast_client, admin_token):
        resp = fast_client.put("/api/admin/config", headers=auth_header(admin_token), json={
            "data_folder": "",
        })
        assert resp.status_code == 422




class TestGetStats:
    @patch("routers.admin.get_index")
    def test_get_stats(self, mock_get_index, fast_client, admin_token):
        mock_index = MagicMock()
        mock_stats = MagicMock()
        mock_stats.number_of_documents = 42
        mock_index.get_stats.return_value = mock_stats
        mock_index.search.return_value = {
            "facetDistribution": {
                "department": {"HR": 10, "Prosjekt": 30, "Driftsmøter": 2},
                "file_type": {"pdf": 20, "docx": 15, "xlsx": 7},
            }
        }
        mock_get_index.return_value = mock_index

        resp = fast_client.get("/api/admin/stats", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_documents"] == 42
        assert "by_department" in data
        assert "by_file_type" in data

    @patch("routers.admin.get_index")
    def test_stats_returns_dicts(self, mock_get_index, fast_client, admin_token):
        mock_index = MagicMock()
        mock_stats = MagicMock()
        mock_stats.number_of_documents = 0
        mock_index.get_stats.return_value = mock_stats
        mock_get_index.return_value = mock_index

        resp = fast_client.get("/api/admin/stats", headers=auth_header(admin_token))
        data = resp.json()
        assert isinstance(data["by_department"], dict)
        assert isinstance(data["by_file_type"], dict)
