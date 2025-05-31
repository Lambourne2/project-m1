from fastapi import APIRouter, Depends
from app.services.redis_service import RedisService
from app.services.calendar_service import CalendarService
import logging

router = APIRouter()
logger = logging.getLogger("app.api.health")

@router.get("")
async def health_check(
    redis_service: RedisService = Depends(),
    calendar_service: CalendarService = Depends()
):
    """
    Health check endpoint.
    
    Checks the status of all required services and returns a health status.
    """
    try:
        # Check Redis connection
        redis_status = await redis_service.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = False
    
    try:
        # Check Google Calendar API
        calendar_status = await calendar_service.check_connection()
    except Exception as e:
        logger.error(f"Google Calendar health check failed: {str(e)}")
        calendar_status = False
    
    # Overall status is healthy only if all services are up
    overall_status = "healthy" if redis_status and calendar_status else "unhealthy"
    
    return {
        "status": overall_status,
        "services": {
            "redis": "up" if redis_status else "down",
            "google_calendar": "up" if calendar_status else "down"
        }
    }
