from fastapi import Depends
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class TwilioWebhook(BaseModel):
    """Model for Twilio SMS webhook data."""
    MessageSid: str
    Body: str
    From: str
    To: str

class Intent(BaseModel):
    """Model for parsed intent data."""
    intent_type: Literal["book", "reschedule", "cancel", "inquiry"] = Literal("intent")
    date: str = ""
    time: str = ""
    service: str = ""
    patient_name: str = ""

class SMSResponse(BaseModel):
    """Model for SMS response data."""
    message: str
    twiml: Optional[str] = None
