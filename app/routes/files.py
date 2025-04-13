from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.file_service import FileService
from app.models.file import FileUploadResponse
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