from fastapi import HTTPException, status
from typing import Optional, Any

class AudioProcessingError(HTTPException):
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        metadata: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.metadata = metadata or {}

class FileValidationError(AudioProcessingError):
    def __init__(self, detail: str, metadata: Optional[dict] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            metadata=metadata
        )

class FileSizeError(FileValidationError):
    def __init__(self, actual_size: float, max_size: int):
        super().__init__(
            detail=f"File size ({actual_size:.2f}MB) exceeds maximum allowed size ({max_size}MB)",
            metadata={"actual_size": actual_size, "max_size": max_size}
        )

class FileFormatError(FileValidationError):
    def __init__(self, content_type: str, supported_formats: set):
        super().__init__(
            detail=f"Unsupported file type: {content_type}. Supported formats: {', '.join(supported_formats)}",
            metadata={"content_type": content_type, "supported_formats": list(supported_formats)}
        )

class AudioDurationError(FileValidationError):
    def __init__(self, actual_duration: float, max_duration: int):
        super().__init__(
            detail=f"Audio duration ({actual_duration:.2f}s) exceeds maximum allowed duration ({max_duration}s)",
            metadata={"actual_duration": actual_duration, "max_duration": max_duration}
        )

class ProcessingError(AudioProcessingError):
    def __init__(self, detail: str, metadata: Optional[dict] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            metadata=metadata
        )

class StorageError(AudioProcessingError):
    def __init__(self, detail: str, metadata: Optional[dict] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            metadata=metadata
        )

class TransactionNotFoundError(AudioProcessingError):
    def __init__(self, transaction_id: str):
        super().__init__(
            detail=f"Transaction not found: {transaction_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            metadata={"transaction_id": transaction_id}
        )

class RedisConnectionError(AudioProcessingError):
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Redis connection error: {detail}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass 