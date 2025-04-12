from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Set, Optional
from enum import Enum

class ServiceType(str, Enum):
    BASIC = "basic"
    FULL = "full"

class AudioProcessingConfig(BaseSettings):
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    max_duration_seconds: float = 300.0
    supported_formats: Set[str] = Field(
        default={
            "wav", "mp3", "ogg", "flac", "m4a", "aac"
        },
        description="Supported audio formats"
    )
    sample_rate: int = Field(default=16000, description="Target sample rate")
    channels: int = Field(default=2, description="Target number of channels")
    storage_path: str = Field(default="uploads", description="Path to store uploaded files")
    processing_timeout: int = Field(default=300, description="Maximum processing time in seconds")
    service_type: ServiceType = ServiceType.BASIC
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0 