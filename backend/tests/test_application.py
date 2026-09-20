from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "milestone": "phase-5-slice"}


def test_settings_defaults_without_env_file() -> None:
    settings = Settings(_env_file=None)
    assert settings.app_env == "local"
    assert settings.database_url.startswith("postgresql+asyncpg://")
