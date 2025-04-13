import os
import uuid
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException
from app.models.file import File, FileType, FileStatus
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