# tests/test_cleanup.py
import os
import time
from pathlib import Path
from cleanup import cleanup_expired
from config import settings


def test_cleanup_removes_old_files_and_keys(client, upload_dir):
    r = client.post("/upload", files={"file": ("old.txt", b"expire me")})
    file_id = r.json()["id"]

    # force mtime to 10 days ago (retention is 3)
    old = time.time() - 10 * 86400
    for p in [upload_dir / file_id, upload_dir / f"{file_id}.meta",
              upload_dir / "keys" / f"{file_id}.key"]:
        os.utime(p, (old, old))

    n = cleanup_expired()
    assert n == 1
    assert not (upload_dir / file_id).exists()
    assert not (upload_dir / "keys" / f"{file_id}.key").exists()
    assert not (upload_dir / f"{file_id}.meta").exists()


def test_cleanup_keeps_fresh_files(client, upload_dir):
    r = client.post("/upload", files={"file": ("new.txt", b"keep me")})
    file_id = r.json()["id"]

    cleanup_expired()
    assert (upload_dir / file_id).exists()
    assert (upload_dir / "keys" / f"{file_id}.key").exists()
