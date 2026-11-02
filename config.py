# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Svipr"
    upload_dir: str = "uploads"
    max_file_size: int = 4 * 1024 * 1024 * 1024
    retention_days: int = 3
    allowed_extensions: str = ""
    upload_rate_limit: str = "10/minute"   # ← add this

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
