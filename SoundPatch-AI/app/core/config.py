from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application Settings
    app_name: str = os.getenv("APP_NAME", "SoundPatch AI")
    app_description: str = os.getenv("APP_DESCRIPTION", "AI-powered audio processing service")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment variables

def get_settings() -> Settings:
    return Settings() 