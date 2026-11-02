import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException

from fastapi.responses import StreamingResponse
from storage import file_path, key_path, meta_path, FileTooLarge, save_upload, CONTEXT
from cryptography.cobblestone import Cobblestone128Decryptor
from config import settings

import asyncio
from cleanup import cleanup_expired

from fastapi.staticfiles import StaticFiles

from fastapi.responses import FileResponse

STATIC_DIR = "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"service": settings.app_name, "status": "ok"}

@app.get("/")
async def index():
    path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(path):
        raise HTTPException(404, "Frontend not built. Run `npm run build` in frontend/")
    return FileResponse(path)

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR, check_dir=False), name="static")


app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        file_id, size = await save_upload(file)
    except FileTooLarge:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_file_size} bytes",
        )
    return {"id": file_id, "size": size, "url": f"/download/{file_id}"}

@app.get("/download/{file_id}")
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async def cleanup_loop():
        while True:
            await asyncio.sleep(3600)  # check every hour
            try:
                n = cleanup_expired()
                if n:
                    print(f"[cleanup] removed {n} expired file(s)")
            except Exception as e:
                print(f"[cleanup] error: {e}")

    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
