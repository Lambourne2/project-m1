from pydantic import BaseModel
from typing import Optional

class Patient(BaseModel):
    """Model for patient data."""
    name: str
    phone_number: str
    email: Optional[str] = None
    last_visit: Optional[str] = None  # YYYY-MM-DD
    next_recall_date: Optional[str] = None  # YYYY-MM-DD
