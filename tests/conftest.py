import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from config import settings
from main import app
from limiter import limiter


@pytest.fixture
def client(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    monkeypatch.setattr(settings, "max_file_size", 1024 * 1024)
    monkeypatch.setattr(settings, "retention_days", 3)
    monkeypatch.setattr(settings, "upload_rate_limit", "1000/minute")

    limiter.reset()

    with TestClient(app) as c:
        yield c


@pytest.fixture
def upload_dir(client):
    return Path(settings.upload_dir)
