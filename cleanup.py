# cleanup.py
import time
from pathlib import Path
from config import settings


def cleanup_expired() -> int:
    """Delete files older than retention_days. Returns count of deleted files."""
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return 0

    cutoff = time.time() - settings.retention_days * 86400
    deleted = 0

    for f in upload_dir.iterdir():
        if not f.is_file():
            continue
        if f.stat().st_mtime >= cutoff:
            continue

        file_id = f.name
        # delete ciphertext
        f.unlink(missing_ok=True)
        # delete key
        (upload_dir / "keys" / f"{file_id}.key").unlink(missing_ok=True)
        # delete meta
        (upload_dir / f"{file_id}.meta").unlink(missing_ok=True)
        deleted += 1

    return deleted


if __name__ == "__main__":
    n = cleanup_expired()
    print(f"Deleted {n} expired file(s)")
