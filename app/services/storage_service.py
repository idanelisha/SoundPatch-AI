import os
import uuid
import aiofiles
from typing import Optional
from app.core.exceptions import StorageError
from app.core.logging import logger
from app.models.config import AudioProcessingConfig

class StorageService:
    def __init__(self, config: AudioProcessingConfig):
        self.config = config
        self.storage_path = config.storage_path
        
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            logger.info("Storage directory created/verified", extra={"path": self.storage_path})
        except OSError as e:
            logger.error("Failed to create storage directory", extra={"error": str(e)})
            raise StorageError(f"Failed to create storage directory: {str(e)}")

    async def save_file(self, file_content: bytes, original_filename: str) -> str:
        """Save the uploaded file and return the file path."""
        try:
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.storage_path, unique_filename)
            
            logger.info("Saving file", extra={
                "original_filename": original_filename,
                "unique_filename": unique_filename,
                "file_size": len(file_content)
            })
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info("File saved successfully", extra={"file_path": file_path})
            return file_path
        except OSError as e:
            logger.error("Failed to save file", extra={"error": str(e)})
            raise StorageError(f"Failed to save file: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("File deleted successfully", extra={"file_path": file_path})
                return True
            return False
        except OSError as e:
            logger.error("Failed to delete file", extra={"error": str(e)})
            raise StorageError(f"Failed to delete file: {str(e)}")

    async def get_file_path(self, filename: str) -> Optional[str]:
        """Get the full path of a file."""
        file_path = os.path.join(self.storage_path, filename)
        return file_path if os.path.exists(file_path) else None 