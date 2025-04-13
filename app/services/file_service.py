import os
import uuid
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException
from app.models.file import File, FileType, FileStatus, ZoomUploadRequest
from app.core.logging import logger

class FileService:
    def __init__(self):
        self.upload_dir = "uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def _get_file_type(self, content_type: str) -> FileType:
        if content_type.startswith("audio/"):
            return FileType.AUDIO
        elif content_type.startswith("video/"):
            return FileType.VIDEO
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only audio and video files are allowed."
            )

    async def upload_file(self, file: UploadFile, title: str) -> File:
        try:
            # Validate file type
            file_type = self._get_file_type(file.content_type)
            
            # Generate unique file ID and transaction ID
            file_id = f"file_{uuid.uuid4().hex[:8]}"
            transaction_id = f"tx_upload_{uuid.uuid4().hex[:8]}"
            
            # Save file
            file_path = os.path.join(self.upload_dir, f"{file_id}_{file.filename}")
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Create file record
            now = datetime.utcnow()
            expiry_date = now + timedelta(days=30)  # 30 days expiry
            
            file_record = File(
                id=file_id,
                title=title,
                type=file_type,
                status=FileStatus.PROCESSING,
                upload_date=now,
                expiry_date=expiry_date,
                transaction_id=transaction_id
            )
            
            logger.info(
                "File uploaded successfully",
                extra={
                    "file_id": file_id,
                    "type": file_type,
                    "title": title
                }
            )
            
            return file_record
            
        except Exception as e:
            logger.error(
                "File upload failed",
                extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file"
            )

    async def upload_zoom_recording(self, request: ZoomUploadRequest) -> File:
        """
        Process a Zoom recording link upload.
        
        Args:
            request: Zoom upload request containing URL and title
            
        Returns:
            File: File record for the Zoom recording
            
        Raises:
            HTTPException: If processing fails
        """
        try:
            # Validate Zoom URL format
            if not request.url.startswith("https://zoom.us/rec/"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Zoom recording URL format"
                )
            
            # Generate unique file ID and transaction ID
            file_id = f"file_{uuid.uuid4().hex[:8]}"
            transaction_id = f"tx_upload_link_{uuid.uuid4().hex[:8]}"
            
            # Create file record
            now = datetime.utcnow()
            expiry_date = now + timedelta(days=30)  # 30 days expiry
            
            file_record = File(
                id=file_id,
                title=request.title,
                type=FileType.ZOOM,
                status=FileStatus.PROCESSING,
                upload_date=now,
                expiry_date=expiry_date,
                transaction_id=transaction_id
            )
            
            # TODO: Implement actual Zoom recording download and processing
            # This is where you would:
            # 1. Download the recording from the Zoom URL
            # 2. Process it as needed
            # 3. Store it in your system
            
            logger.info(
                "Zoom recording link processed successfully",
                extra={
                    "file_id": file_id,
                    "title": request.title,
                    "url": request.url
                }
            )
            
            return file_record
            
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                "Zoom recording processing failed",
                extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to process Zoom recording"
            ) 