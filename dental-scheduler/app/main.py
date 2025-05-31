from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings
from app.core.scheduler import ReminderScheduler
from app.services.calendar_service import CalendarService
from app.services.twilio_service import TwilioService
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application")
    
    # Initialize services
    calendar_service = CalendarService()
    twilio_service = TwilioService()
    
    # Initialize and start reminder scheduler
    scheduler = ReminderScheduler(calendar_service, twilio_service)
    await scheduler.start()
    
    # Store scheduler in app state
    app.state.scheduler = scheduler
    
    logger.info("Application startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")
    
    # Stop reminder scheduler
    if hasattr(app.state, "scheduler"):
        await app.state.scheduler.stop()
    
    logger.info("Application shutdown complete")
