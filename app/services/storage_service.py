import os
import uuid
import aiofiles
from typing import Optional
from app.core.config import StorageConfig
from app.core.exceptions import StorageError
from app.core.logging import logger
from fastapi import UploadFile, HTTPException

class StorageService:
    def __init__(self, config: StorageConfig):
        self.storage_path = config.storage_path
        self._ensure_storage_directory()

    def _ensure_storage_directory(self) -> None:
        """
        Ensure the storage directory exists.
        """
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            logger.info(f"Storage directory ensured at {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize storage directory"
            )

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

    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        """
        Upload a file to the storage directory.
        
        Args:
            file: The file to upload
            file_path: The path where to store the file (relative to storage_path)
            
        Returns:
            str: The full path to the uploaded file
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Create the full path
            full_path = os.path.join(self.storage_path, file_path)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file
            async with aiofiles.open(full_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            logger.info(
                "File uploaded successfully",
                extra={
                    "file_path": file_path,
                    "size": len(content),
                    "content_type": file.content_type
                }
            )
            
            return full_path
            
        except Exception as e:
            logger.error(
                "File upload failed",
                extra={
                    "error": str(e),
                    "file_path": file_path
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file"
            )

    async def get_file_content(self, file_path: str) -> Optional[bytes]:
        """
        Get the content of a file from storage.
        
        Args:
            file_path: The path to the file (relative to storage_path)
            
        Returns:
            Optional[bytes]: The file content if found, None otherwise
            
        Raises:
            HTTPException: If reading fails
        """
        try:
            # Create the full path
            full_path = os.path.join(self.storage_path, file_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                logger.warning(
                    "File not found in storage",
                    extra={"file_path": file_path}
                )
                return None
            
            # Read the file
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
            
            logger.info(
                "File content retrieved successfully",
                extra={
                    "file_path": file_path,
                    "size": len(content)
                }
            )
            
            return content
            
        except Exception as e:
            logger.error(
                "Failed to read file content",
                extra={
                    "error": str(e),
                    "file_path": file_path
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to read file content"
            ) 