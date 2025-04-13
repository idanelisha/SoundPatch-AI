import json
from typing import Any, Dict, List, Optional, Union
from redis import asyncio as aioredis
from app.core.config import RedisConfig
from app.core.logging import logger

class RedisService:
    def __init__(self, config: RedisConfig):
        self.redis = aioredis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            decode_responses=True
        )

    async def hset(self, key: str, field: str, value: Union[str, dict]) -> bool:
        """
        Set the value of a hash field.
        
        Args:
            key: Redis key
            field: Hash field
            value: Value to set (string or dict)
            
        Returns:
            bool: True if field was set, False if field already existed
        """
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            return await self.redis.hset(key, field, value)
        except Exception as e:
            logger.error(f"Failed to set hash field: {str(e)}")
            raise

    async def hget(self, key: str, field: str) -> Optional[str]:
        """
        Get the value of a hash field.
        
        Args:
            key: Redis key
            field: Hash field
            
        Returns:
            Optional[str]: Field value or None if not found
        """
        try:
            return await self.redis.hget(key, field)
        except Exception as e:
            logger.error(f"Failed to get hash field: {str(e)}")
            raise

    async def hgetall(self, key: str) -> Dict[str, str]:
        """
        Get all fields and values in a hash.
        
        Args:
            key: Redis key
            
        Returns:
            Dict[str, str]: Dictionary of field-value pairs
        """
        try:
            return await self.redis.hgetall(key)
        except Exception as e:
            logger.error(f"Failed to get all hash fields: {str(e)}")
            raise

    async def hdel(self, key: str, *fields: str) -> int:
        """
        Delete one or more hash fields.
        
        Args:
            key: Redis key
            *fields: Fields to delete
            
        Returns:
            int: Number of fields deleted
        """
        try:
            return await self.redis.hdel(key, *fields)
        except Exception as e:
            logger.error(f"Failed to delete hash fields: {str(e)}")
            raise

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            return await self.redis.exists(key)
        except Exception as e:
            logger.error(f"Failed to check key existence: {str(e)}")
            raise

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set a key's time to live in seconds.
        
        Args:
            key: Redis key
            seconds: Time to live in seconds
            
        Returns:
            bool: True if timeout was set, False if key does not exist
        """
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Failed to set key expiration: {str(e)}")
            raise

    async def ttl(self, key: str) -> int:
        """
        Get the time to live of a key in seconds.
        
        Args:
            key: Redis key
            
        Returns:
            int: Time to live in seconds, -1 if key exists but has no TTL,
                 -2 if key does not exist
        """
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get key TTL: {str(e)}")
            raise

    async def set(self, key: str, value: Union[str, dict], ex: Optional[int] = None) -> bool:
        """
        Set the value of a key.
        
        Args:
            key: Redis key
            value: Value to set (string or dict)
            ex: Optional expiration time in seconds
            
        Returns:
            bool: True if key was set
        """
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            return await self.redis.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Failed to set key: {str(e)}")
            raise

    async def get(self, key: str) -> Optional[str]:
        """
        Get the value of a key.
        
        Args:
            key: Redis key
            
        Returns:
            Optional[str]: Key value or None if not found
        """
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Failed to get key: {str(e)}")
            raise

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            int: Number of keys deleted
        """
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete keys: {str(e)}")
            raise

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Find all keys matching the given pattern.
        
        Args:
            pattern: Pattern to match
            
        Returns:
            List[str]: List of matching keys
        """
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"Failed to get keys: {str(e)}")
            raise

    async def close(self) -> None:
        """
        Close the Redis connection.
        """
        try:
            await self.redis.close()
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {str(e)}")
            raise 