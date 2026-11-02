# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Svipr"
    upload_dir: str = "uploads"
    max_file_size: int = 4 * 1024 * 1024 * 1024  # 4 GB
    retention_days: int = 3
    allowed_extensions: str = ""  # empty = allow all

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
