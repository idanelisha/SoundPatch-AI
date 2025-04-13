from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
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

class FileListItem(BaseModel):
    id: str
    title: str
    type: FileType
    status: FileStatus
    uploadDate: datetime
    expiryDate: datetime

class PaginationInfo(BaseModel):
    total: int
    page: int
    limit: int
    totalPages: int

class FileListResponse(BaseModel):
    files: List[FileListItem]
    pagination: PaginationInfo
    transaction_id: str 