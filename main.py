# main.py
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException

from fastapi.responses import StreamingResponse
from storage import file_path, key_path, meta_path, FileTooLarge, save_upload, CONTEXT
from cryptography.cobblestone import Cobblestone128Decryptor
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        file_id, size = await save_upload(file)
    except FileTooLarge:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_file_size} bytes",
        )
    return {"id": file_id, "size": size, "url": f"/{file_id}"}

@app.get("/{file_id}")
async def download(file_id: str):
    fpath = file_path(file_id)
    kpath = key_path(file_id)
    if not fpath.exists() or not kpath.exists():
        raise HTTPException(404, "File not found or expired")

    key = kpath.read_bytes()
    original = meta_path(file_id).read_text(encoding="utf-8") if meta_path(file_id).exists() else file_id

    def decrypt_stream():
        decryptor = Cobblestone128Decryptor(key, context=CONTEXT)
        with fpath.open("rb") as f:
            while chunk := f.read(1024 * 1024):
                yield decryptor.update(chunk)
            yield decryptor.finalize()

    return StreamingResponse(
        decrypt_stream(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{original}"'},
    )
