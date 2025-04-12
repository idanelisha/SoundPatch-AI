import os
import json
import librosa
from redis.asyncio import Redis
import soundfile as sf
import numpy as np
from datetime import datetime, UTC
from typing import Optional
import io
from app.models.config import AudioProcessingConfig
from app.core.exceptions import (
    RedisConnectionError,
    StorageError,
    ProcessingError,
    AudioDurationError,
    TransactionNotFoundError
)
from app.core.logging import logger
from app.services.storage_service import StorageService

class BaseAudioService:
    def __init__(self, config: AudioProcessingConfig):
        self.config = config
        logger.info("Initializing BaseAudioService", extra={"config": config.dict()})
        self.storage_service = StorageService(config)

        try:
            self.redis_client = Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=config.redis_db,
                decode_responses=True  # This ensures we get strings instead of bytes
            )
            logger.info("Successfully initialized Redis client")
        except Exception as e:
            logger.error("Failed to initialize Redis client", extra={"error": str(e)})
            raise RedisConnectionError(f"Failed to initialize Redis client: {str(e)}")

    def preprocess_audio(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Basic audio preprocessing without model-specific steps."""
        try:
            # Resample to 16kHz if necessary
            if sr != 16000:
                y = librosa.resample(y, orig_sr=sr, target_sr=16000)
            return y
            
        except Exception as e:
            logger.error("Failed to preprocess audio", extra={"error": str(e)})
            raise ProcessingError(f"Failed to preprocess audio: {str(e)}")

    async def process_audio(self, file_path: str) -> dict:
        """Process the audio file and return metadata."""
        logger.info("Starting audio processing", extra={"file_path": file_path})
        
        try:
            # Load audio file
            try:
                y, sr = librosa.load(file_path)
                logger.debug("Audio file loaded", extra={"sample_rate": sr})
            except Exception as e:
                logger.error("Failed to load audio file", extra={"error": str(e), "file_path": file_path})
                raise ProcessingError(f"Failed to load audio file: {str(e)}")
            
            # Get audio metadata
            try:
                duration = librosa.get_duration(y=y, sr=sr)
                duration_seconds = float(duration)
                logger.debug("Audio duration calculated", extra={"duration": duration_seconds})
            except Exception as e:
                logger.error("Failed to get audio duration", extra={"error": str(e)})
                raise ProcessingError(f"Failed to get audio duration: {str(e)}")
            
            # Validate duration
            if duration_seconds > self.config.max_duration_seconds:
                logger.warning("Audio duration exceeds limit", extra={
                    "duration": duration_seconds,
                    "max_duration": self.config.max_duration_seconds
                })
                raise AudioDurationError(duration_seconds, self.config.max_duration_seconds)
            
            # Preprocess audio
            try:
                processed_audio = self.preprocess_audio(y, sr)
                logger.debug("Audio preprocessed successfully")
            except Exception as e:
                logger.error("Failed to preprocess audio", extra={"error": str(e)})
                raise ProcessingError(f"Failed to preprocess audio: {str(e)}")
            
            # Save processed audio
            try:
                processed_filename = os.path.basename(file_path).replace('.', '_processed.')
                
                # Use BytesIO to write audio data to memory
                audio_buffer = io.BytesIO()
                sf.write(audio_buffer, processed_audio, sr, format='wav')
                audio_buffer.seek(0)  # Reset buffer position to beginning
                
                processed_path = await self.storage_service.save_file(
                    audio_buffer.read(),
                    processed_filename
                )
                logger.info("Saving processed audio", extra={"processed_path": processed_path})
            except Exception as e:
                logger.error("Failed to save processed audio", extra={"error": str(e)})
                raise StorageError(f"Failed to save processed audio: {str(e)}")
            
            result = {
                "duration": duration_seconds,
                "sample_rate": sr,
                "channels": 2 if len(y.shape) > 1 else 1,
                "processed_path": processed_path,
                "status": "completed"
            }
            
            logger.info("Audio processing completed successfully", extra=result)
            return result
            
        except (ProcessingError, StorageError, AudioDurationError):
            raise
        except Exception as e:
            logger.error("Unexpected error during audio processing", extra={"error": str(e)})
            raise ProcessingError(f"Unexpected error during audio processing: {str(e)}") 
        
    async def update_transaction_status(self, transaction_id: str, status: str, metadata: Optional[dict] = None):
        """Update the transaction status in Redis."""
        try:
            key = f"transaction:{transaction_id}"
            status_data = {
                "status": status,
                "updated_at": datetime.now(UTC).isoformat(),
                "metadata": json.dumps(metadata) if metadata else "{}"
            }
            logger.debug("Updating transaction status", extra={
                "transaction_id": transaction_id,
                "redis_key": key,
                "status": status,
                "metadata": metadata
            })
            
            # Store the data
            await self.redis_client.hmset(key, status_data)
            
            # Verify the data was stored
            stored_data = await self.redis_client.hgetall(key)
            logger.debug("Verified stored data", extra={
                "transaction_id": transaction_id,
                "stored_data": stored_data
            })
            
            if not stored_data:
                logger.error("Failed to verify stored data", extra={"transaction_id": transaction_id})
                raise RedisConnectionError("Failed to verify stored data")
                
            logger.info("Transaction status updated successfully", extra={
                "transaction_id": transaction_id,
                "status": status
            })
        except Exception as e:
            logger.error("Failed to update transaction status", extra={
                "error": str(e),
                "transaction_id": transaction_id,
                "status": status,
                "error_type": type(e).__name__
            })
            raise RedisConnectionError(f"Failed to update transaction status: {str(e)}")

    async def get_transaction_status(self, transaction_id: str) -> Optional[dict]:
        """Get the transaction status from Redis."""
        try:
            key = f"transaction:{transaction_id}"
            logger.debug("Getting transaction status", extra={
                "transaction_id": transaction_id,
                "redis_key": key
            })
            
            # First check if the key exists
            exists = await self.redis_client.exists(key)
            logger.debug("Checked if key exists", extra={
                "transaction_id": transaction_id,
                "exists": exists
            })
            
            if not exists:
                logger.warning("Transaction key does not exist", extra={"transaction_id": transaction_id})
                raise TransactionNotFoundError(transaction_id)
            
            # Get the status data
            status_data = await self.redis_client.hgetall(key)
            logger.debug("Retrieved status data", extra={
                "transaction_id": transaction_id,
                "status_data": status_data
            })
            
            if not status_data:
                logger.warning("Transaction exists but has no data", extra={"transaction_id": transaction_id})
                raise TransactionNotFoundError(transaction_id)
            
            # Parse the metadata JSON string back into a dictionary
            if "metadata" in status_data:
                try:
                    status_data["metadata"] = json.loads(status_data["metadata"])
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse metadata JSON", extra={
                        "error": str(e),
                        "transaction_id": transaction_id
                    })
                    status_data["metadata"] = {}
                
            logger.debug("Transaction status retrieved successfully", extra={
                "transaction_id": transaction_id,
                "status": status_data.get("status")
            })
            return status_data
            
        except TransactionNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get transaction status", extra={
                "error": str(e),
                "transaction_id": transaction_id,
                "error_type": type(e).__name__
            })
            raise RedisConnectionError(f"Failed to get transaction status: {str(e)}")
            
    async def save_file(self, content: bytes, filename: str) -> str:
        """
        Save a file using the storage service.
        
        Args:
            content: The file content as bytes
            filename: The original filename
            
        Returns:
            str: The path where the file was saved
            
        Raises:
            StorageError: If saving the file fails
        """
        try:
            logger.debug("Saving file", extra={"filename": filename})
            file_path = await self.storage_service.save_file(content, filename)
            logger.info("File saved successfully", extra={"file_path": file_path})
            return file_path
        except Exception as e:
            logger.error("Failed to save file", extra={
                "error": str(e),
                "filename": filename,
                "error_type": type(e).__name__
            })
            raise StorageError(f"Failed to save file: {str(e)}") 