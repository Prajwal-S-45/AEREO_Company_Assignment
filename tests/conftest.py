import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

@pytest.fixture
def client(tmp_path, monkeypatch):
    import app.config as config
    db = tmp_path / "test.db"
    cert_dir = tmp_path / "certificates"
    cert_dir.mkdir()
    monkeypatch.setattr(config, "DB_PATH", db)
    monkeypatch.setattr(config, "CERTIFICATES_DIR", cert_dir)
    import app.database as database
    monkeypatch.setattr(database, "DB_PATH", db)
    import app.services as services
    monkeypatch.setattr(services.config, "CERTIFICATES_DIR", cert_dir)
    init_db()
    with TestClient(app) as test_client:
        yield test_client
