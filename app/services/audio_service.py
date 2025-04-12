import os
import json
import librosa
import numpy as np
import tensorflow as tf
from datetime import datetime, UTC
from typing import Optional
from redis.asyncio import Redis
from app.models.config import AudioProcessingConfig
from app.core.exceptions import (
    StorageError,
    ProcessingError,
    AudioDurationError,
    RedisConnectionError,
    TransactionNotFoundError
)
from app.core.logging import logger
from app.services.base_audio_service import BaseAudioService

class AudioService(BaseAudioService):
    def __init__(self, config: AudioProcessingConfig):
        super().__init__(config)
        logger.info("Initializing AudioService", extra={"config": config.dict()})
        
        try:
            # Load the trained model
            model_path = 'models/best_light_model.keras'
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            self.model = tf.keras.models.load_model(model_path)
            logger.info("Successfully loaded the trained model")
        except Exception as e:
            logger.error("Failed to load the trained model", extra={"error": str(e)})
            raise ProcessingError(f"Failed to load the trained model: {str(e)}")

    def preprocess_audio(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Preprocess the audio for model prediction."""
        try:
            # Resample to 16kHz if necessary
            if sr != 16000:
                y = librosa.resample(y, orig_sr=sr, target_sr=16000)
            
            # Extract mel spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y,
                sr=16000,
                n_mels=64,
                hop_length=160,
                n_fft=400
            )
            
            # Convert to log scale
            mel_spec_db = librosa.power_to_db(mel_spec)
            
            # Add channel dimension
            mel_spec_db = np.expand_dims(mel_spec_db, axis=-1)
            
            return mel_spec_db
            
        except Exception as e:
            logger.error("Failed to preprocess audio", extra={"error": str(e)})
            raise ProcessingError(f"Failed to preprocess audio: {str(e)}")

    async def process_audio(self, file_path: str) -> dict:
        """Process the audio file and return metadata."""
        # First get the basic processing result from parent class
        result = await super().process_audio(file_path)
        
        try:
            # Load audio file for model prediction
            y, sr = librosa.load(file_path)
            
            # Preprocess for model
            mel_spec = self.preprocess_audio(y, sr)
            
            # Make prediction
            try:
                # Pad or truncate to match training data length if needed
                if mel_spec.shape[1] > 1000:  # MAX_T from training
                    mel_spec = mel_spec[:, :1000, :]
                
                prediction = self.model.predict(np.expand_dims(mel_spec, axis=0))
                # The model outputs a sequence of probabilities for each time step
                predictions = prediction[0].flatten()
                logger.debug("Model prediction completed", extra={
                    "prediction_shape": predictions.shape
                })
                
                # Add predictions to result
                result["predictions"] = {
                    "sequence": predictions.tolist(),
                    "shape": predictions.shape
                }
                
            except Exception as e:
                logger.error("Failed to make model prediction", extra={"error": str(e)})
                raise ProcessingError(f"Failed to make model prediction: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error("Unexpected error during audio processing", extra={"error": str(e)})
            raise ProcessingError(f"Unexpected error during audio processing: {str(e)}")
