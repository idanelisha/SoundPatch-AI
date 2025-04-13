from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class FileType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    ZOOM = "zoom"

class FileStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class File(BaseModel):
    id: str
    title: str
    type: FileType
    status: FileStatus
    upload_date: datetime
    expiry_date: datetime
    transaction_id: str

class FileUploadResponse(BaseModel):
    id: str
    title: str
    type: FileType
    status: FileStatus
    uploadDate: datetime
    expiryDate: datetime
    transaction_id: str

class ZoomUploadRequest(BaseModel):
    url: str
    title: str 