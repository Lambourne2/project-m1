from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TimeSlot(BaseModel):
    """Model for available time slot."""
    date: str  # YYYY-MM-DD
    time: str  # HH:MM

class Appointment(BaseModel):
    """Model for appointment data."""
    id: Optional[str] = None
    service: str
    patient_name: str
    phone_number: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    end_time: Optional[str] = None  # HH:MM
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
