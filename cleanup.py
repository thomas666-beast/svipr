import time
from pathlib import Path

from config import settings
from meta import read_meta


def cleanup_expired() -> int:
    """Delete files past retention_days. Returns count of file IDs removed."""
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return 0

    cutoff = time.time() - settings.retention_days * 86400
    deleted = 0

    for f in upload_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix in {".meta", ".part", ".key"}:
            continue

        file_id = f.name
        meta = read_meta(file_id)

        # no meta = orphan, delete it
        # meta with uploaded_at < cutoff = expired, delete it
        # otherwise keep
        if meta.uploaded_at is not None and meta.uploaded_at >= cutoff:
            continue

        f.unlink(missing_ok=True)
        (upload_dir / "keys" / f"{file_id}.key").unlink(missing_ok=True)
        (upload_dir / f"{file_id}.meta").unlink(missing_ok=True)
        deleted += 1

    return deleted


if __name__ == "__main__":
    print(f"Deleted {cleanup_expired()} expired file(s)")
