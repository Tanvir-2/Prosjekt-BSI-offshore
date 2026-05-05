import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parent
_raw_data_folder = os.getenv("DATA_FOLDER", str(PROJECT_ROOT.parent / "tilgang" / "tilgang"))
if not Path(_raw_data_folder).is_absolute():
    _raw_data_folder = str(PROJECT_ROOT / _raw_data_folder)
DATA_FOLDER = str(Path(_raw_data_folder).resolve())


MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_KEY = os.getenv("MEILISEARCH_KEY", "bsiSecretKey123")
MEILISEARCH_INDEX = "bsi_documents"


JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8

# ── Server ─────────────────────────────────────────────────
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'users.db'}")


SKIP_EXTENSIONS = {'.lnk'}

# Valid roles in the system
VALID_ROLES = {"admin", "hr", "project_manager"}


ROLE_DEPARTMENT_ACCESS = {
    "admin": None,           
    "hr": ["HR", "Driftsmøter"],
    "project_manager": ["Prosjekt", "Driftsmøter"],
}
