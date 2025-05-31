from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config import settings
from app.models.appointment import Appointment, TimeSlot
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("app.services.calendar")

class CalendarService:
    """
    Service for interacting with Google Calendar.
    
    This service handles:
    - Checking appointment availability
    - Creating, updating, and canceling appointments
    - Finding alternative time slots
    - Retrieving upcoming appointments for reminders
    """
    
    def __init__(self):
        """Initialize the Calendar service."""
        # Set up Google Calendar credentials
        self.credentials = Credentials.from_authorized_user_info(
            info={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": settings.google_refresh_token
            }
        )
        
        # Build Google Calendar service
        self.service = build("calendar", "v3", credentials=self.credentials)
        self.calendar_id = "primary"
        self.time_zone = "America/Denver"  # Utah time zone
    
    async def check_connection(self) -> bool:
        """
        Check if Google Calendar API is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        try:
            # Try to get calendar metadata
            self.service.calendars().get(calendarId=self.calendar_id).execute()
            return True
        except Exception as e:
            logger.error(f"Google Calendar connection check failed: {str(e)}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def check_availability(self, date: str, time: str) -> bool:
        """
        Check if a time slot is available.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            
        Returns:
            True if available, False otherwise
        """
        try:
            # Convert date and time to datetime
            start_time = datetime.fromisoformat(f"{date}T{time}:00")
            end_time = start_time + timedelta(hours=1)
            
            # Check for existing events
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat() + "Z",
                timeMax=end_time.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            
            # If no events found, slot is available
            return len(events) == 0
        
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def create_appointment(
        self,
        date: str,
        time: str,
        service: str,
        patient_name: str,
        phone_number: str
    ) -> Appointment:
        """
        Create a new appointment.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            service: Service type (e.g., "Cleaning")
            patient_name: Patient's name
            phone_number: Patient's phone number
            
        Returns:
            Created appointment
        """
        try:
            # Convert date and time to datetime
            start_time = datetime.fromisoformat(f"{date}T{time}:00")
            end_time = start_time + timedelta(hours=1)
            
            # Create event
            event = {
                "summary": f"{service} - {patient_name}",
                "description": phone_number,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": self.time_zone
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": self.time_zone
                }
            }
            
            # Insert event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Created appointment: {created_event['id']}")
            
            # Return appointment
            return Appointment(
                id=created_event["id"],
                service=service,
                patient_name=patient_name,
                phone_number=phone_number,
                date=date,
                time=time,
                end_time=end_time.strftime("%H:%M"),
                created_at=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def update_appointment(
        self,
        appointment_id: str,
        new_date: str,
        new_time: str
    ) -> Appointment:
        """
        Update an existing appointment.
        
        Args:
            appointment_id: Appointment ID
            new_date: New date in YYYY-MM-DD format
            new_time: New time in HH:MM format
            
        Returns:
            Updated appointment
        """
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=appointment_id
            ).execute()
            
            # Extract appointment details
            summary_parts = event["summary"].split(" - ", 1)
            service = summary_parts[0] if len(summary_parts) > 0 else "Appointment"
            patient_name = summary_parts[1] if len(summary_parts) > 1 else "Patient"
            phone_number = event.get("description", "")
            
            # Convert new date and time to datetime
            start_time = datetime.fromisoformat(f"{new_date}T{new_time}:00")
            end_time = start_time + timedelta(hours=1)
            
            # Update event times
            event["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": self.time_zone
            }
            event["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": self.time_zone
            }
            
            # Update event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=appointment_id,
                body=event
            ).execute()
            
            logger.info(f"Updated appointment: {updated_event['id']}")
            
            # Return updated appointment
            return Appointment(
                id=updated_event["id"],
                service=service,
                patient_name=patient_name,
                phone_number=phone_number,
                date=new_date,
                time=new_time,
                end_time=end_time.strftime("%H:%M"),
                updated_at=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def cancel_appointment(self, appointment_id: str) -> bool:
        """
        Cancel an appointment.
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete event
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=appointment_id
            ).execute()
            
            logger.info(f"Canceled appointment: {appointment_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error canceling appointment: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def find_appointment_by_phone(self, phone_number: str) -> Appointment:
        """
        Find an appointment by phone number.
        
        Args:
            phone_number: Patient's phone number
            
        Returns:
            Appointment if found, None otherwise
        """
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone_number(phone_number)
            
            # Get upcoming events
            now = datetime.utcnow()
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat() + "Z",
                maxResults=10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            
            # Find event with matching phone number
            for event in events:
                if event.get("description") == normalized_phone:
                    # Extract appointment details
                    summary_parts = event["summary"].split(" - ", 1)
                    service = summary_parts[0] if len(summary_parts) > 0 else "Appointment"
                    patient_name = summary_parts[1] if len(summary_parts) > 1 else "Patient"
                    
                    # Extract date and time
                    start = datetime.fromisoformat(
                        event["start"]["dateTime"].replace("Z", "")
                    )
                    end = datetime.fromisoformat(
                        event["end"]["dateTime"].replace("Z", "")
                    )
                    
                    # Return appointment
                    return Appointment(
                        id=event["id"],
                        service=service,
                        patient_name=patient_name,
                        phone_number=normalized_phone,
                        date=start.strftime("%Y-%m-%d"),
                        time=start.strftime("%H:%M"),
                        end_time=end.strftime("%H:%M")
                    )
            
            # No matching appointment found
            return None
        
        except Exception as e:
            logger.error(f"Error finding appointment by phone: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def find_alternatives(self, date: str, requested_time: str) -> list[TimeSlot]:
        """
        Find alternative time slots.
        
        Args:
            date: Date in YYYY-MM-DD format
            requested_time: Requested time in HH:MM format
            
        Returns:
            List of available time slots
        """
        try:
            # Convert date and time to datetime
            requested_datetime = datetime.fromisoformat(f"{date}T{requested_time}:00")
            
            # Define time range to search (9 AM to 5 PM)
            start_of_day = datetime.fromisoformat(f"{date}T09:00:00")
            end_of_day = datetime.fromisoformat(f"{date}T17:00:00")
            
            # Get all events for the day
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_of_day.isoformat() + "Z",
                timeMax=end_of_day.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            
            # Find available slots
            available_slots = []
            current_time = start_of_day
            
            while current_time < end_of_day:
                slot_end = current_time + timedelta(hours=1)
                
                # Check if slot overlaps with any event
                is_available = True
                for event in events:
                    event_start = datetime.fromisoformat(
                        event["start"]["dateTime"].replace("Z", "")
                    )
                    event_end = datetime.fromisoformat(
                        event["end"]["dateTime"].replace("Z", "")
                    )
                    
                    if (current_time < event_end and slot_end > event_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(
                        TimeSlot(
                            date=date,
                            time=current_time.strftime("%H:%M")
                        )
                    )
                
                # Move to next hour
                current_time += timedelta(hours=1)
            
            # Sort by proximity to requested time
            available_slots.sort(
                key=lambda slot: abs(
                    datetime.fromisoformat(f"{date}T{slot.time}:00") - requested_datetime
                )
            )
            
            # Return top 2 alternatives
            return available_slots[:2]
        
        except Exception as e:
            logger.error(f"Error finding alternatives: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def get_appointments_for_reminders(self, hours_ahead: int) -> list[Appointment]:
        """
        Get appointments for sending reminders.
        
        Args:
            hours_ahead: Hours ahead to look for appointments
            
        Returns:
            List of appointments
        """
        try:
            # Calculate time window
            now = datetime.utcnow()
            target_time = now + timedelta(hours=hours_ahead)
            start_time = target_time - timedelta(minutes=30)
            end_time = target_time + timedelta(minutes=30)
            
            # Get events in time window
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat() + "Z",
                timeMax=end_time.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            
            # Convert events to appointments
            appointments = []
            for event in events:
                # Extract appointment details
                summary_parts = event["summary"].split(" - ", 1)
                service = summary_parts[0] if len(summary_parts) > 0 else "Appointment"
                patient_name = summary_parts[1] if len(summary_parts) > 1 else "Patient"
                phone_number = event.get("description", "")
                
                # Extract date and time
                start = datetime.fromisoformat(
                    event["start"]["dateTime"].replace("Z", "")
                )
                end = datetime.fromisoformat(
                    event["end"]["dateTime"].replace("Z", "")
                )
                
                # Add appointment
                appointments.append(
                    Appointment(
                        id=event["id"],
                        service=service,
                        patient_name=patient_name,
                        phone_number=phone_number,
                        date=start.strftime("%Y-%m-%d"),
                        time=start.strftime("%H:%M"),
                        end_time=end.strftime("%H:%M")
                    )
                )
            
            return appointments
        
        except Exception as e:
            logger.error(f"Error getting appointments for reminders: {str(e)}")
            raise
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Ensure phone number is in E.164 format.
        
        Args:
            phone_number: Phone number to normalize
            
        Returns:
            Normalized phone number
        """
        # Remove any non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Ensure phone number is in E.164 format
        if not phone_number.startswith("+"):
            if digits_only.startswith("1") and len(digits_only) == 11:
                return f"+{digits_only}"
            elif len(digits_only) == 10:
                return f"+1{digits_only}"
            else:
                return f"+{digits_only}"
        
        return phone_number
