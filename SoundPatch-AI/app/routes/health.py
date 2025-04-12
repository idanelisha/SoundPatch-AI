from fastapi import APIRouter, HTTPException, status
from app.services.service_factory import create_audio_service
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService
from app.models.config import AudioProcessingConfig
from app.core.logging import logger

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

# Initialize services
try:
    config = AudioProcessingConfig()
    audio_service = create_audio_service(config)
    auth_service = AuthService()
    storage_service = StorageService(config)
    logger.info("Services initialized for health check")
except Exception as e:
    logger.error("Failed to initialize services for health check", extra={"error": str(e)})
    raise

@router.get("")
async def health_check():
    """Check the health of all services."""
    health_status = {
        "status": "healthy",
        "services": {
            "redis": {"status": "healthy", "message": "Connected"},
            "firebase": {"status": "healthy", "message": "Connected"},
            "storage": {"status": "healthy", "message": "Accessible"}
        }
    }
    
    try:
        # Check Redis
        try:
            audio_service.redis_client.ping()
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["status"] = "unhealthy"
            logger.error("Redis health check failed", extra={"error": str(e)})
        
        # Check Firebase
        try:
            auth_service.db.collection("health_check").document("test").get()
        except Exception as e:
            health_status["services"]["firebase"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["status"] = "unhealthy"
            logger.error("Firebase health check failed", extra={"error": str(e)})
        
        # Check Storage
        try:
            storage_service.get_file_path("test.txt")
        except Exception as e:
            health_status["services"]["storage"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["status"] = "unhealthy"
            logger.error("Storage health check failed", extra={"error": str(e)})
        
        if health_status["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
        
        logger.info("Health check completed successfully")
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "error": str(e)}
        ) 