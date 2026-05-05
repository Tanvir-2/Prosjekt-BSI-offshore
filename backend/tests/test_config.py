import os
import pytest
from pathlib import Path


class TestConfig:
    """Tests for config.py settings and constants."""

    def test_data_folder_exists(self):
        """DATA_FOLDER should point to a real directory."""
        from config import DATA_FOLDER
        assert os.path.isdir(DATA_FOLDER), f"DATA_FOLDER does not exist: {DATA_FOLDER}"

    def test_data_folder_has_departments(self):
        """DATA_FOLDER should contain the 3 BSI departments."""
        from config import DATA_FOLDER
        subfolders = os.listdir(DATA_FOLDER)
        for dept in ["Prosjekt", "HR", "Driftsmøter"]:
            assert dept in subfolders, f"Missing department folder: {dept}"

    def test_data_folder_path_default(self):
        """DATA_FOLDER default should resolve to tilgang/tilgang."""
        from config import DATA_FOLDER, PROJECT_ROOT
        expected = str(PROJECT_ROOT.parent / "tilgang" / "tilgang")
        assert DATA_FOLDER == expected

    def test_meilisearch_defaults(self):
        """Meilisearch config should have sensible defaults."""
        from config import MEILISEARCH_URL, MEILISEARCH_KEY, MEILISEARCH_INDEX
        assert MEILISEARCH_URL == "http://localhost:7700"
        assert MEILISEARCH_KEY == "bsiSecretKey123"
        assert MEILISEARCH_INDEX == "bsi_documents"

    def test_jwt_defaults(self):
        """JWT config should have correct defaults."""
        from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS
        assert JWT_SECRET == "change-this-secret-in-production"
        assert JWT_ALGORITHM == "HS256"
        assert JWT_EXPIRE_HOURS == 8

    def test_skip_extensions(self):
        """SKIP_EXTENSIONS should only contain .lnk."""
        from config import SKIP_EXTENSIONS
        assert SKIP_EXTENSIONS == {'.lnk'}

    def test_valid_roles(self):
        """VALID_ROLES should match the 3 BSI roles."""
        from config import VALID_ROLES
        assert VALID_ROLES == {"admin", "hr", "project_manager"}

    def test_role_department_access_keys(self):
        """ROLE_DEPARTMENT_ACCESS should have entries for all valid roles."""
        from config import VALID_ROLES, ROLE_DEPARTMENT_ACCESS
        assert set(ROLE_DEPARTMENT_ACCESS.keys()) == VALID_ROLES

    def test_role_department_access_values(self):
        """Each role should have correct department access."""
        from config import ROLE_DEPARTMENT_ACCESS
        assert ROLE_DEPARTMENT_ACCESS["admin"] is None
        assert "HR" in ROLE_DEPARTMENT_ACCESS["hr"]
        assert "Driftsmøter" in ROLE_DEPARTMENT_ACCESS["hr"]
        assert "Prosjekt" in ROLE_DEPARTMENT_ACCESS["project_manager"]
        assert "Driftsmøter" in ROLE_DEPARTMENT_ACCESS["project_manager"]

    def test_database_url_default(self):
        """DATABASE_URL should default to SQLite file in backend folder."""
        from config import DATABASE_URL, PROJECT_ROOT
        assert DATABASE_URL.startswith("sqlite:///")
        assert "users.db" in DATABASE_URL

    def test_project_root_is_backend_folder(self):
        """PROJECT_ROOT should be the backend/ folder."""
        from config import PROJECT_ROOT
        assert PROJECT_ROOT.name == "backend"
        assert PROJECT_ROOT.is_dir()

    def test_env_file_exists(self):
        """A .env file should exist in the backend folder."""
        from config import PROJECT_ROOT
        env_path = PROJECT_ROOT / ".env"
        assert env_path.exists(), ".env file missing from backend/"

    def test_frontend_url_default(self):
        """FRONTEND_URL should point to Vite dev server."""
        from config import FRONTEND_URL
        assert FRONTEND_URL == "http://localhost:5173"
