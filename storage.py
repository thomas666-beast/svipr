# storage.py
import secrets
import shutil
from pathlib import Path
from typing import AsyncIterator

from fastapi import UploadFile

from config import settings

CHUNK_SIZE = 1024 * 1024  # 1 MB chunks


def generate_file_id() -> str:
    """URL-safe, unpredictable ID. 16 bytes = ~22 chars of entropy."""
    return secrets.token_urlsafe(16)


def file_path(file_id: str) -> Path:
    return Path(settings.upload_dir) / file_id


def meta_path(file_id: str) -> Path:
    return Path(settings.upload_dir) / f"{file_id}.meta"


class FileTooLarge(Exception):
    pass


async def save_upload(upload: UploadFile) -> tuple[str, int]:
    """
    Stream an upload to disk with a size cap.
    Returns (file_id, bytes_written).
    Raises FileTooLarge if the limit is exceeded.
    """
    file_id = generate_file_id()
    final = file_path(file_id)
    tmp = final.with_suffix(".part")

    written = 0
    try:
        with tmp.open("wb") as out:
            while chunk := await upload.read(CHUNK_SIZE):
                written += len(chunk)
                if written > settings.max_file_size:
                    raise FileTooLarge
                out.write(chunk)
        tmp.rename(final)  # atomic on same filesystem
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    # Store the original filename as metadata, sanitized for display only
    original = (upload.filename or "file").replace("\x00", "").strip()[:255]
    meta_path(file_id).write_text(original, encoding="utf-8")

    return file_id, written
