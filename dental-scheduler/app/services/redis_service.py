import aioredis
from app.config import settings
import json
import logging

logger = logging.getLogger("app.services.redis")

class RedisService:
    """
    Redis service for state management and caching.
    
    This service provides methods for interacting with Redis, including:
    - Setting and getting values
    - Managing conversation state
    - Caching LLM responses
    """
    
    def __init__(self):
        """Initialize the Redis service."""
        self.redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        self.redis = None
    
    async def _get_connection(self):
        """Get a Redis connection."""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                self.redis_url,
                password=settings.redis_password,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis
    
    async def ping(self) -> bool:
        """
        Check if Redis is available.
        
        Returns:
            True if Redis is available, False otherwise
        """
        try:
            redis = await self._get_connection()
            return await redis.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False
    
    async def get(self, key: str) -> dict:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Value as a dictionary
        """
        try:
            redis = await self._get_connection()
            value = await redis.get(key)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: dict, expire: int = None) -> bool:
        """
        Set a value in Redis.
        
        Args:
            key: Redis key
            value: Value to set
            expire: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = await self._get_connection()
            serialized = json.dumps(value)
            
            if expire:
                await redis.setex(key, expire, serialized)
            else:
                await redis.set(key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = await self._get_connection()
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {str(e)}")
            return False
    
    async def cache_llm_response(self, prompt: str, response: str) -> bool:
        """
        Cache an LLM response.
        
        Args:
            prompt: LLM prompt
            response: LLM response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a cache key from the prompt
            import hashlib
            key = f"llm:cache:{hashlib.md5(prompt.encode()).hexdigest()}"
            
            # Store the response with a 24-hour expiration
            return await self.set(key, {"response": response}, expire=86400)
        except Exception as e:
            logger.error(f"LLM cache failed: {str(e)}")
            return False
    
    async def get_cached_llm_response(self, prompt: str) -> str:
        """
        Get a cached LLM response.
        
        Args:
            prompt: LLM prompt
            
        Returns:
            Cached response or None
        """
        try:
            # Create a cache key from the prompt
            import hashlib
            key = f"llm:cache:{hashlib.md5(prompt.encode()).hexdigest()}"
            
            # Get the cached response
            cached = await self.get(key)
            
            if cached:
                return cached.get("response")
            return None
        except Exception as e:
            logger.error(f"Get LLM cache failed: {str(e)}")
            return None
