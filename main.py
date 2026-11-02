# main.py
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException

from config import settings
from storage import save_upload, FileTooLarge


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
