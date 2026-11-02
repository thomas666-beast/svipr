# tests/test_cleanup.py
import os
import time
from pathlib import Path
from cleanup import cleanup_expired
from config import settings
from meta import meta_path


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


def _age_meta(file_id: str, seconds: int):
    """Rewrite the uploaded_at line in meta to N seconds ago."""
    p = meta_path(file_id)
    lines = p.read_text(encoding="utf-8").split("\n")
    lines[2] = str(int(time.time()) - seconds)
    p.write_text("\n".join(lines), encoding="utf-8")


def test_cleanup_removes_old_files_and_keys(client, upload_dir):
    r = client.post("/upload", files={"file": ("old.txt", b"expire me")})
    file_id = r.json()["id"]

    _age_meta(file_id, 10 * 86400)  # 10 days ago

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


def test_cleanup_deletes_orphan_without_meta(client, upload_dir):
    # simulate a crashed upload: ciphertext on disk, no meta
    orphan = upload_dir / "orphanid"
    orphan.write_bytes(b"leftover ciphertext")

    n = cleanup_expired()
    assert n == 1
    assert not orphan.exists()
