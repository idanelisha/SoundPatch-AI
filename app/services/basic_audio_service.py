from app.core.config import RedisConfig, StorageConfig
from app.services.base_audio_service import BaseAudioService
from app.models.config import AudioProcessingConfig
from app.core.logging import logger

class BasicAudioService(BaseAudioService):
    def __init__(self, config: AudioProcessingConfig, storage_config: StorageConfig, redis_config: RedisConfig):
        super().__init__(config, storage_config, redis_config)
        logger.info("Initializing BasicAudioService") 