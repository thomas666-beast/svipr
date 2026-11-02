from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    with_key: int = 0
    app_name: str = "svipr"
    upload_dir: str = "uploads"
    max_file_size: int = 4 * 1024 * 1024 * 1024  # 4 GB
    retention_days: int = 3
    donate: int = 0

    donate_btc: str = "bc1q..."
    donate_xmr: str = "4..."
    donate_usdt: str = "T..."
    
    # NEW: Rate limiting
    upload_rate_limit: str = "3/30 minutes" 

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
