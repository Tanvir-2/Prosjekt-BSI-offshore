import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_returns_ok_status(self, client):
        assert client.get("/health").json()["status"] == "ok"

    def test_health_returns_service_name(self, client):
        assert client.get("/health").json()["service"] == "BSI Search Engine"

    def test_health_response_has_expected_keys(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert "service" in data
        assert "watcher" in data


class TestLifespan:
    """Tests for the startup lifespan handler."""

    def test_lifespan_creates_tables(self):
        """Lifespan handler should create tables on startup."""
        from database import Base, engine
        from sqlalchemy import inspect as sa_inspect

        Base.metadata.drop_all(bind=engine)
        assert "users" not in sa_inspect(engine).get_table_names()

        from main import app
        with TestClient(app) as client:
            tables = sa_inspect(engine).get_table_names()
            assert "users" in tables
            assert "audit_logs" in tables

    def test_health_works_after_startup(self, client):
        assert client.get("/health").status_code == 200


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_allows_frontend_origin(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_allows_credentials(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_rejects_unknown_origin(self, client):
        response = client.get(
            "/health",
            headers={"Origin": "http://evil-site.com"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") != "http://evil-site.com"


class TestOpenAPI:
    """Tests for auto-generated API docs."""

    def test_openapi_json_accessible(self, client):
        assert client.get("/openapi.json").status_code == 200

    def test_openapi_has_health_endpoint(self, client):
        assert "/health" in client.get("/openapi.json").json()["paths"]

    def test_swagger_ui_accessible(self, client):
        assert client.get("/docs").status_code == 200

    def test_app_title_set(self, client):
        assert client.get("/openapi.json").json()["info"]["title"] == "BSI Document Search Engine"


class TestWatcherIntegration:
    """Tests for watcher start/stop with FastAPI lifespan."""

    def test_watcher_status_in_health(self, client):
        data = client.get("/health").json()
        assert "watcher" in data
        assert "running" in data["watcher"]
        assert "watch_path" in data["watcher"]
        assert "pending_index" in data["watcher"]

    def test_watcher_running_during_lifespan(self, client):
        from main import watcher
        assert watcher.is_running is True

    def test_watcher_status_is_true_in_health(self, client):
        data = client.get("/health").json()
        assert data["watcher"]["running"] is True

    def test_watcher_stops_after_lifespan(self):
        from main import app, watcher
        with TestClient(app):
            assert watcher.is_running is True
        assert watcher.is_running is False
