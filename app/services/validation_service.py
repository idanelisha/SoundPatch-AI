from fastapi import UploadFile
from app.models.config import AudioProcessingConfig
from app.core.exceptions import FileValidationError, FileSizeError, FileFormatError
from app.core.logging import logger

class ValidationService:
    def __init__(self, config: AudioProcessingConfig):
        self.config = config

    async def validate_audio_file(self, file: UploadFile) -> bytes:
        """
        Validate the uploaded audio file and return its content.
        
        Args:
            file: The uploaded file to validate
            
        Returns:
            bytes: The validated file content
            
        Raises:
            FileValidationError: If any validation fails
        """
        # Validate file type
        self._validate_file_type(file.content_type)
        
        # Read and validate file content
        content = await file.read()
        self._validate_file_size(content)
        
        return content

    def _validate_file_type(self, content_type: str) -> None:
        """Validate the file content type."""
        # Map MIME types to file extensions
        mime_to_extension = {
            "audio/mpeg": "mp3",
            "audio/wav": "wav",
            "audio/wave": "wav",
            "audio/x-wav": "wav",
            "audio/ogg": "ogg",
            "audio/flac": "flac",
            "audio/x-flac": "flac",
            "audio/mp4": "m4a",
            "audio/aac": "aac",
            "audio/x-aac": "aac"
        }
        
        # Get the file extension from the MIME type
        file_extension = mime_to_extension.get(content_type.lower())
        
        if not file_extension or file_extension not in self.config.supported_formats:
            logger.warning("Unsupported file type", extra={
                "content_type": content_type,
                "supported_formats": list(self.config.supported_formats)
            })
            raise FileFormatError(content_type, self.config.supported_formats)

    def _validate_file_size(self, content: bytes) -> None:
        """Validate the file size."""
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            logger.warning("File size exceeds limit", extra={
                "file_size": file_size_mb,
                "max_size": self.config.max_file_size_mb
            })
            raise FileSizeError(file_size_mb, self.config.max_file_size_mb) 