import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.models.file import (
    File, FileType, FileStatus, ZoomUploadRequest,
    FileListItem, PaginationInfo, FileListResponse
)
from app.core.logging import logger

class FileService:
    def __init__(self):
        self.upload_dir = "uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        # TODO: Initialize database connection
        self.files = []  # This should be replaced with actual database storage

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
            
            # TODO: Store in database
            self.files.append(file_record)
            
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
            
            # TODO: Store in database
            self.files.append(file_record)
            
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

    async def list_files(
        self,
        status: Optional[FileStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> FileListResponse:
        """
        List files with optional filtering and pagination.
        
        Args:
            status: Filter by file status
            search: Search term for file title
            page: Page number (1-based)
            limit: Number of items per page
            
        Returns:
            FileListResponse: List of files with pagination info
        """
        try:
            # Generate transaction ID
            transaction_id = f"tx_get_files_{uuid.uuid4().hex[:8]}"
            
            # TODO: Replace with actual database query
            filtered_files = self.files.copy()
            
            # Apply status filter
            if status:
                filtered_files = [f for f in filtered_files if f.status == status]
            
            # Apply search filter
            if search:
                search_lower = search.lower()
                filtered_files = [
                    f for f in filtered_files
                    if search_lower in f.title.lower()
                ]
            
            # Calculate pagination
            total = len(filtered_files)
            total_pages = (total + limit - 1) // limit
            page = max(1, min(page, total_pages))
            
            # Get paginated results
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_files = filtered_files[start_idx:end_idx]
            
            # Convert to response format
            file_items = [
                FileListItem(
                    id=f.id,
                    title=f.title,
                    type=f.type,
                    status=f.status,
                    uploadDate=f.upload_date,
                    expiryDate=f.expiry_date
                )
                for f in paginated_files
            ]
            
            pagination_info = PaginationInfo(
                total=total,
                page=page,
                limit=limit,
                totalPages=total_pages
            )
            
            logger.info(
                "Files listed successfully",
                extra={
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "status": status,
                    "has_search": bool(search)
                }
            )
            
            return FileListResponse(
                files=file_items,
                pagination=pagination_info,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to list files",
                extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to list files"
            ) 