from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UploadResponse(BaseModel):
    transaction_id: str
    filename: str
    timestamp: datetime
    status: str = "pending"
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "audio_sample.wav",
                "timestamp": "2024-03-29T12:00:00",
                "status": "pending"
            }
        } 