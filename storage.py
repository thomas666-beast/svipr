# storage.py
import secrets
from pathlib import Path
from fastapi import UploadFile
from cryptography.cobblestone import Cobblestone128Encryptor, Cobblestone128Decryptor
from config import settings

CHUNK_SIZE = 1024 * 1024
CONTEXT = b"svipr-v1"  # bound context, decryptor must use same value

class FileTooLarge(Exception):
    pass

def generate_file_id() -> str:
    return secrets.token_urlsafe(16)

def file_path(file_id: str) -> Path:
    return Path(settings.upload_dir) / file_id

def key_path(file_id: str) -> Path:
    # keys in separate directory, not alongside ciphertext
    return Path(settings.upload_dir) / "keys" / f"{file_id}.key"

def meta_path(file_id: str) -> Path:
    return Path(settings.upload_dir) / f"{file_id}.meta"

async def save_upload(upload: UploadFile) -> tuple[str, int]:
    file_id = generate_file_id()
    final = file_path(file_id)
    tmp = final.with_suffix(".part")
    kpath = key_path(file_id)
    kpath.parent.mkdir(parents=True, exist_ok=True)

    key = Cobblestone128Encryptor.generate_key()  # 16-byte random key
    encryptor = Cobblestone128Encryptor(key, context=CONTEXT)

    written = 0
    try:
        with tmp.open("wb") as out:
            while chunk := await upload.read(CHUNK_SIZE):
                written += len(chunk)
                if written > settings.max_file_size:
                    raise FileTooLarge
                out.write(encryptor.update(chunk))  # stream encrypt
            out.write(encryptor.finalize())
        tmp.rename(final)
        kpath.write_bytes(key)  # key stored separately from ciphertext
    except Exception:
        tmp.unlink(missing_ok=True)
        kpath.unlink(missing_ok=True)
        raise

    original = (upload.filename or "file").replace("\x00", "").strip()[:255]
    meta_path(file_id).write_text(original, encoding="utf-8")
    return file_id, written
