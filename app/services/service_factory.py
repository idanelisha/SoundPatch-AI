from app.core.config import RedisConfig, StorageConfig
from app.models.config import AudioProcessingConfig, ServiceType
from app.services.audio_service import AudioService
from app.services.basic_audio_service import BasicAudioService
from app.core.logging import logger

def create_audio_service(config: AudioProcessingConfig, storage_config: StorageConfig, redis_config: RedisConfig):
    """Factory function to create the appropriate audio service based on configuration."""
    logger.info(f"Creating audio service of type: {config.service_type}")
    
    if config.service_type == ServiceType.BASIC:
        return BasicAudioService(config, storage_config, redis_config)
    elif config.service_type == ServiceType.FULL:
        return AudioService(config, storage_config, redis_config)
    else:
        raise ValueError(f"Unknown service type: {config.service_type}") 