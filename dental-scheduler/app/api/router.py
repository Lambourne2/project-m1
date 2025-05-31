from fastapi import APIRouter

api_router = APIRouter()

# Import and include sub-routers
from app.api.twilio import router as twilio_router
from app.api.health import router as health_router

api_router.include_router(twilio_router, prefix="/twilio", tags=["twilio"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
