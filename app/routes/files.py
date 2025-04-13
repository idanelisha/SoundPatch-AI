from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from app.services.file_service import FileService
from app.models.file import (
    FileUploadResponse, ZoomUploadRequest,
    FileListResponse, FileStatus, FileDetails
)
from app.core.logging import logger
from app.core.config import get_settings   

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

# Initialize file service
try:
    settings = get_settings()
    file_service = FileService(settings.storage, settings.redis)
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

@router.get("/{file_id}", response_model=FileDetails)
async def get_file_details(file_id: str):
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
        return await file_service.get_file_details(file_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to get file details", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Failed to get file details"
        )

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    version: str = Query("processed", description="Version of the file to download (processed or original)")
):
    """
    Download a file by its ID.
    
    Args:
        file_id: The ID of the file to download
        version: The version of the file to download (processed or original)
        
    Returns:
        Response: Binary file data with appropriate headers
        
    Raises:
        HTTPException: If file not found or download fails
    """
    try:
        content, content_type, filename = await file_service.download_file(file_id, version)
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("File download failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Failed to download file"
        ) 