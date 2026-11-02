# main.py
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)

@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "ok"}
