from app.services.base_audio_service import BaseAudioService
from app.models.config import AudioProcessingConfig
from app.core.logging import logger

class BasicAudioService(BaseAudioService):
    def __init__(self, config: AudioProcessingConfig):
        super().__init__(config)
        logger.info("Initializing BasicAudioService") 