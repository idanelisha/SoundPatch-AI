from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from app.services.file_service import FileService
from app.models.file import (
    FileUploadResponse, ZoomUploadRequest,
    FileListResponse, FileStatus
)
from app.core.logging import logger

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

# Initialize file service
try:
    file_service = FileService()
    logger.info("File service initialized successfully")
except Exception as e:
    logger.error("Failed to initialize file service", extra={"error": str(e)})
    raise

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...)
):
    """
    Upload a file (audio or video).
    
    Args:
        file: The file to upload (audio or video)
        title: The title of the file
        
    Returns:
        FileUploadResponse: Information about the uploaded file
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        file_record = await file_service.upload_file(file, title)
        
        # Convert to response format
        return FileUploadResponse(
            id=file_record.id,
            title=file_record.title,
            type=file_record.type,
            status=file_record.status,
            uploadDate=file_record.upload_date,
            expiryDate=file_record.expiry_date,
            transaction_id=file_record.transaction_id
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("File upload failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Failed to upload file"
        )

@router.post("/upload-link", response_model=FileUploadResponse)
async def upload_zoom_recording(request: ZoomUploadRequest):
    """
    Upload a Zoom recording link.
    
    Args:
        request: Zoom upload request containing URL and title
        
    Returns:
        FileUploadResponse: Information about the uploaded recording
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        file_record = await file_service.upload_zoom_recording(request)
        
        # Convert to response format
        return FileUploadResponse(
            id=file_record.id,
            title=file_record.title,
            type=file_record.type,
            status=file_record.status,
            uploadDate=file_record.upload_date,
            expiryDate=file_record.expiry_date,
            transaction_id=file_record.transaction_id
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Zoom recording upload failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Failed to process Zoom recording"
        )

@router.get("", response_model=FileListResponse)
async def list_files(
    status: FileStatus = Query(None, description="Filter by file status"),
    search: str = Query(None, description="Search term for file title"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    List files with optional filtering and pagination.
    
    Args:
        status: Filter by file status
        search: Search term for file title
        page: Page number (1-based)
        limit: Number of items per page
        
    Returns:
        FileListResponse: List of files with pagination info
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        return await file_service.list_files(
            status=status,
            search=search,
            page=page,
            limit=limit
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to list files", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Failed to list files"
        ) 