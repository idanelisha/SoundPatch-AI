import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.core.config import RedisConfig, StorageConfig
from app.models.file import (
    File, FileType, FileStatus, ZoomUploadRequest,
    FileListItem, PaginationInfo, FileListResponse, FileDetails
)
from app.core.logging import logger
from app.services.storage_service import StorageService
from app.services.redis_service import RedisService
import json

class FileService:
    def __init__(self, storage_config: StorageConfig, redis_config: RedisConfig):
        self.storage_service = StorageService(storage_config)
        self.redis_service = RedisService(redis_config)
        self.files_key = "files"
        self.transactions_key = "transactions"

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
            
            # Save file to storage
            file_path = f"{file_id}_original"
            await self.storage_service.upload_file(file, file_path)
            
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
            
            # Save file record to Redis
            await self.redis_service.hset(
                self.files_key,
                file_id,
                file_record.json()
            )
            
            # Save transaction to Redis
            transaction_data = {
                "id": transaction_id,
                "file_id": file_id,
                "status": "processing",
                "created_at": now.isoformat(),
                "type": "file_upload"
            }
            await self.redis_service.hset(
                self.transactions_key,
                transaction_id,
                json.dumps(transaction_data)
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
            
            # Save file record to Redis
            await self.redis_service.hset(
                self.files_key,
                file_id,
                file_record.json()
            )
            
            # Save transaction to Redis
            transaction_data = {
                "id": transaction_id,
                "file_id": file_id,
                "status": "processing",
                "created_at": now.isoformat(),
                "type": "zoom_upload",
                "url": request.url
            }
            await self.redis_service.hset(
                self.transactions_key,
                transaction_id,
                json.dumps(transaction_data)
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
            # Get all files from Redis
            files_data = await self.redis_service.hgetall(self.files_key)
            files = [File.parse_raw(data) for data in files_data.values()]
            
            # Apply status filter
            if status:
                files = [f for f in files if f.status == status]
            
            # Apply search filter
            if search:
                search_lower = search.lower()
                files = [
                    f for f in files
                    if search_lower in f.title.lower()
                ]
            
            # Calculate pagination
            total = len(files)
            total_pages = (total + limit - 1) // limit
            page = max(1, min(page, total_pages))
            
            # Get paginated results
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_files = files[start_idx:end_idx]
            
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
                pagination=pagination_info
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

    async def get_file_details(self, file_id: str) -> FileDetails:
        """
        Get detailed information about a file.
        
        Args:
            file_id: The ID of the file to get details for
            
        Returns:
            FileDetails: Detailed file information
            
        Raises:
            HTTPException: If file not found or other error occurs
        """
        try:
            # Get file record from Redis
            file_data = await self.redis_service.hget(self.files_key, file_id)
            if not file_data:
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
            
            file_record = File.parse_raw(file_data)
            
            # TODO: Get additional file details from your storage service
            # This is where you would:
            # 1. Get file size from storage
            # 2. Get duration from media processing service
            # 3. Get URLs from your CDN/storage service
            # 4. Get description from your database
            
            # For now, using placeholder values
            file_details = FileDetails(
                id=file_record.id,
                title=file_record.title,
                type=file_record.type,
                status=file_record.status,
                uploadDate=file_record.upload_date,
                expiryDate=file_record.expiry_date,
                description="This is a sample description for the recording.",
                duration="1:23:47",
                fileSize="345.7 MB",
                mediaUrl=f"https://storage.example.com/processed-files/{file_id}.mp4",
                originalMediaUrl=f"https://storage.example.com/original-files/{file_id}.mp4"
            )
            
            logger.info(
                "File details retrieved successfully",
                extra={
                    "file_id": file_id,
                    "type": file_record.type,
                    "status": file_record.status
                }
            )
            
            return file_details
            
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                "Failed to get file details",
                extra={
                    "error": str(e),
                    "file_id": file_id
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to get file details"
            )

    async def download_file(self, file_id: str, version: str = "processed") -> tuple[bytes, str, str]:
        """
        Download a file by its ID.
        
        Args:
            file_id: The ID of the file to download
            version: The version of the file to download ("processed" or "original")
            
        Returns:
            tuple[bytes, str, str]: The file content, content type, and filename
            
        Raises:
            HTTPException: If file not found or download fails
        """
        try:
            # Get file record from Redis
            file_data = await self.redis_service.hget(self.files_key, file_id)
            if not file_data:
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
            
            file_record = File.parse_raw(file_data)
            
            # Determine file path based on version
            if version == "processed":
                file_path = f"{file_id}_processed"
            else:
                file_path = f"{file_id}_original"
            
            # Get file content from storage
            content = await self.storage_service.get_file_content(file_path)
            if not content:
                raise HTTPException(
                    status_code=404,
                    detail="File content not found"
                )
            
            # Determine content type based on file type
            content_type = "audio/mpeg" if file_record.type == FileType.AUDIO else "video/mp4"
            
            # Create filename
            extension = ".mp3" if file_record.type == FileType.AUDIO else ".mp4"
            filename = f"{file_record.title}{extension}"
            
            logger.info(
                "File download prepared successfully",
                extra={
                    "file_id": file_id,
                    "version": version,
                    "type": file_record.type
                }
            )
            
            return content, content_type, filename
            
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                "Failed to download file",
                extra={
                    "error": str(e),
                    "file_id": file_id,
                    "version": version
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to download file"
            )

    async def stream_file(self, file_id: str, version: str = "processed", range_header: Optional[str] = None) -> tuple[Optional[bytes], str, int, int, int]:
        """
        Stream a file by its ID with support for range requests.
        
        Args:
            file_id: The ID of the file to stream
            version: The version of the file to stream ("processed" or "original")
            range_header: The Range header from the request
            
        Returns:
            tuple[Optional[bytes], str, int, int, int]: 
                - File content chunk
                - Content type
                - Start byte
                - End byte
                - Total file size
                
        Raises:
            HTTPException: If file not found or streaming fails
        """
        try:
            # Get file record from Redis
            file_data = await self.redis_service.hget(self.files_key, file_id)
            if not file_data:
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
            
            file_record = File.parse_raw(file_data)
            
            # Determine file path based on version
            if version == "processed":
                file_path = f"{file_id}_processed"
            else:
                file_path = f"{file_id}_original"
            
            # Stream file content from storage
            content, content_type, start_byte, end_byte = await self.storage_service.stream_file(file_path, range_header)
            if content is None:
                raise HTTPException(
                    status_code=404,
                    detail="File content not found"
                )
            
            # Get total file size
            total_size = os.path.getsize(os.path.join(self.storage_service.storage_path, file_path))
            
            logger.info(
                "File streaming prepared successfully",
                extra={
                    "file_id": file_id,
                    "version": version,
                    "type": file_record.type,
                    "start_byte": start_byte,
                    "end_byte": end_byte,
                    "total_size": total_size
                }
            )
            
            return content, content_type, start_byte, end_byte, total_size
            
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                "Failed to stream file",
                extra={
                    "error": str(e),
                    "file_id": file_id,
                    "version": version
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to stream file"
            ) 