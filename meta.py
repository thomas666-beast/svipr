# meta.py
from dataclasses import dataclass
from pathlib import Path

from config import settings


@dataclass
class FileMeta:
    filename: str
    size: int | None
    uploaded_at: int | None


def meta_path(file_id: str) -> Path:
    return Path(settings.upload_dir) / f"{file_id}.meta"


def read_meta(file_id: str) -> FileMeta:
    p = meta_path(file_id)
    if not p.exists():
        return FileMeta(filename=file_id, size=None, uploaded_at=None)

    lines = p.read_text(encoding="utf-8").split("\n")
    filename = lines[0] or file_id
    try:
        size = int(lines[1]) if len(lines) > 1 else None
    except ValueError:
        size = None
    try:
        uploaded_at = int(lines[2]) if len(lines) > 2 else None
    except ValueError:
        uploaded_at = None
    return FileMeta(filename=filename, size=size, uploaded_at=uploaded_at)
