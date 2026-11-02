import os
import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from cryptography.cobblestone import Cobblestone128Decryptor

from contextvars import ContextVar

from config import settings
from storage import file_path, key_path, FileTooLarge, save_upload, CONTEXT
from cleanup import cleanup_expired
from meta import read_meta, meta_path
from limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import json

STATIC_DIR = "static"

current_request: ContextVar[Request | None] = ContextVar("current_request", default=None)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async def cleanup_loop():
        while True:
            await asyncio.sleep(3600)
            try:
                n = cleanup_expired()
                if n:
                    print(f"[cleanup] removed {n} expired file(s)")
            except Exception as e:
                print(f"[cleanup] error: {e}")

    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/api/health")
async def health():
    return {
        "service": settings.app_name,
        "status": "ok",
        "max_file_size": settings.max_file_size,
        "retention_days": settings.retention_days,
        "with_key": settings.with_key,
        "donate": settings.donate,
    }

@app.get("/")
async def index():
    path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(path):
        raise HTTPException(404, "Frontend not built. Run `npm run build` in frontend/")
    return FileResponse(path)


@app.middleware("http")
async def set_request_context(request: Request, call_next):
    current_request.set(request)
    return await call_next(request)


def get_upload_limit() -> str:
    req = current_request.get()
    if req and req.headers.get("X-Svipr-Key"):
        return "1000/minute"
    return settings.upload_rate_limit


@app.post("/upload")
@limiter.limit(get_upload_limit)
async def upload(request: Request, file: UploadFile = File(...)):
    verify_key(request)  # <-- Rejects invalid keys with 403 before saving
    try:
        file_id, size = await save_upload(file)
    except FileTooLarge:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_file_size} bytes",
        )
    return {"id": file_id, "size": size, "url": f"/download/{file_id}"}



@app.get("/download/{file_id}/raw")
async def download_raw(file_id: str):
    fpath = file_path(file_id)
    kpath = key_path(file_id)
    if not fpath.exists() or not kpath.exists():
        raise HTTPException(404, "File not found or expired")

    key = kpath.read_bytes()
    original = (
        meta_path(file_id).read_text(encoding="utf-8").split("\n", 1)[0]
        if meta_path(file_id).exists() else file_id
    )

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


@app.get("/download/{file_id}")
async def download_page(file_id: str):
    if not file_path(file_id).exists():
        raise HTTPException(404, "File not found or expired")

    meta = read_meta(file_id)
    expires_at = None
    if meta.uploaded_at is not None:
        expires_at = meta.uploaded_at + settings.retention_days * 86400

    from download_page import render_download_page
    return HTMLResponse(
        render_download_page(file_id, meta.filename, meta.size, expires_at)
    )


@app.get("/api/info/{file_id}")
async def file_info(file_id: str):
    fpath = file_path(file_id)
    if not fpath.exists():
        raise HTTPException(404, "File not found or expired")

    meta = read_meta(file_id)
    expires_at = None
    if meta.uploaded_at is not None:
        expires_at = meta.uploaded_at + settings.retention_days * 86400

    return {
        "id": file_id,
        "filename": meta.filename,
        "size": meta.size,
        "uploaded_at": meta.uploaded_at,
        "expires_at": expires_at,
        "download_url": f"/download/{file_id}/raw",
    }

def verify_key(request: Request):
    """Checks the X-Svipr-Key header if WITH_KEY=1"""
    if settings.with_key != 1:
        return  # Public mode, allow everyone

    key = request.headers.get("X-Svipr-Key")
    if not key:
        raise HTTPException(status_code=401, detail="Missing access key")

    try:
        with open("keys.json", "r") as f:
            valid_keys = json.load(f).get("keys", [])
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Server config error: keys.json not found")

    if key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid access key")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR, check_dir=False), name="static")
