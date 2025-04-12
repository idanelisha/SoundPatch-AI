import uuid
from datetime import datetime, UTC
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from app.models.upload import UploadResponse
from app.models.config import AudioProcessingConfig
from app.models.user import User
from app.services.service_factory import create_audio_service
from app.services.validation_service import ValidationService
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.core.exceptions import (
    FileValidationError,
    FileSizeError,
    FileFormatError,
    ProcessingError,
    StorageError,
    RedisConnectionError,
    TransactionNotFoundError
)
from app.core.logging import logger

router = APIRouter(
    prefix="/audio",
    tags=["audio"]
)

# Initialize configuration and services
config = AudioProcessingConfig()
try:
    logger.info("Initializing audio routes")
    audio_service = create_audio_service(config)
    validation_service = ValidationService(config)
    auth_service = AuthService()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error("Failed to initialize services", extra={"error": str(e)})
    raise ProcessingError("Failed to initialize services")

async def process_audio_background(transaction_id: str, file_path: str, user_id: str):
    """Background task to process audio file."""
    logger.info("Starting background audio processing", extra={
        "transaction_id": transaction_id,
        "file_path": file_path,
        "user_id": user_id
    })
    
    try:
        # Update status to processing
        await audio_service.update_transaction_status(transaction_id, "processing")
        logger.debug("Updated status to processing", extra={"transaction_id": transaction_id})
        
        # Process the audio
        result = await audio_service.process_audio(file_path)
        logger.info("Audio processing completed", extra={
            "transaction_id": transaction_id,
            "result": result
        })
        
        # Update final status
        await audio_service.update_transaction_status(
            transaction_id,
            result["status"],
            result
        )
        
        # Update user's transaction history
        await auth_service.update_user_transactions(
            user_id,
            transaction_id,
            {
                "filename": file_path.split("/")[-1],
                "status": result["status"],
                "duration": result.get("duration"),
                "sample_rate": result.get("sample_rate")
            }
        )
        
        logger.debug("Updated final status and user history", extra={"transaction_id": transaction_id})
    except Exception as e:
        logger.error("Error in background processing", extra={
            "transaction_id": transaction_id,
            "error": str(e)
        })
        # Update status with error
        await audio_service.update_transaction_status(
            transaction_id,
            "error",
            {"error": str(e)}
        )

@router.post("/upload", response_model=UploadResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an audio file and receive a transaction ID for tracking.
    
    Args:
        file: The audio file to upload
        current_user: The authenticated user
        
    Returns:
        UploadResponse: Contains transaction ID and file information
        
    Raises:
        FileValidationError: If file format or size is invalid
        StorageError: If file storage fails
        ProcessingError: If processing setup fails
    """
    logger.info("Received file upload request", extra={
        "uploaded_filename": file.filename,
        "user_id": current_user.id
    })
    
    try:
        # Validate file and get content
        content = await validation_service.validate_audio_file(file)
        
        # Generate transaction ID
        transaction_id = str(uuid.uuid4())
        logger.debug("Generated transaction ID", extra={"transaction_id": transaction_id})
        
        # Initialize transaction in Redis with initial status
        await audio_service.update_transaction_status(
            transaction_id,
            "pending",
            {
                "filename": file.filename,
                "user_id": current_user.id,
                "upload_time": datetime.now(UTC).isoformat()
            }
        )
        
        # Save file
        file_path = await audio_service.save_file(content, file.filename)
        logger.info("File saved successfully", extra={"file_path": file_path})
        
        # Add background task for processing
        background_tasks.add_task(
            process_audio_background,
            transaction_id,
            file_path,
            current_user.id
        )
        logger.debug("Added background processing task", extra={"transaction_id": transaction_id})
        
        # Create response
        response = UploadResponse(
            transaction_id=transaction_id,
            filename=file.filename,
            timestamp=datetime.now(UTC)
        )
        
        logger.info("File upload completed successfully", extra={
            "transaction_id": transaction_id,
            "uploaded_filename": file.filename,
            "user_id": current_user.id
        })
        return response
        
    except (FileValidationError, StorageError, ProcessingError):
        raise
    except Exception as e:
        logger.error("Unexpected error during file upload", extra={"error": str(e)})
        raise ProcessingError(f"Unexpected error during file upload: {str(e)}")

@router.get("/status/{transaction_id}")
async def get_status(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of an audio processing transaction.
    
    Args:
        transaction_id: The transaction ID to check
        current_user: The authenticated user
        
    Returns:
        dict: Status information including processing metadata
        
    Raises:
        TransactionNotFoundError: If transaction ID is not found
        RedisConnectionError: If Redis connection fails
    """
    logger.info("Received status check request", extra={
        "transaction_id": transaction_id,
        "user_id": current_user.id
    })
    
    try:
        status = await audio_service.get_transaction_status(transaction_id)
        logger.debug("Retrieved transaction status", extra={
            "transaction_id": transaction_id,
            "status": status
        })
        return status
    except (TransactionNotFoundError, RedisConnectionError):
        raise
    except Exception as e:
        logger.error("Unexpected error while getting status", extra={
            "transaction_id": transaction_id,
            "error": str(e)
        })
        raise ProcessingError(f"Unexpected error while getting status: {str(e)}") 