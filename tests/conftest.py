# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from config import settings
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # point upload_dir to a temp dir per test
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    monkeypatch.setattr(settings, "max_file_size", 1024 * 1024)  # 1 MB
    monkeypatch.setattr(settings, "retention_days", 3)

    with TestClient(app) as c:
        yield c


@pytest.fixture
def upload_dir(client):
    return Path(settings.upload_dir)

@pytest.fixture
def raw_url():
    return lambda fid: f"/download/{fid}/raw"
