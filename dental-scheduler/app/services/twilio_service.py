from twilio.rest import Client
from app.config import settings
from app.models.message import SMSResponse
import logging
from twilio.base.exceptions import TwilioRestException
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("app.services.twilio")

class TwilioService:
    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.phone_number = settings.twilio_phone_number
        self.client = Client(self.account_sid, self.auth_token)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def send_sms(self, to: str, body: str) -> str:
        """
        Send an SMS message using Twilio.
        
        Args:
            to: Recipient phone number (E.164 format)
            body: Message content
            
        Returns:
            Message SID
        """
        try:
            # Normalize phone number
            normalized_to = self._normalize_phone_number(to)
            
            # Send message
            message = self.client.messages.create(
                body=body,
                from_=self.phone_number,
                to=normalized_to
            )
            
            logger.info(f"SMS sent to {normalized_to}: {body[:50]}...")
            return message.sid
        
        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {to}: {str(e)}")
            raise
    
    async def send_booking_confirmation(self, appointment, phone_number: str) -> str:
        """
        Send a booking confirmation SMS.
        
        Args:
            appointment: Appointment data
            phone_number: Recipient phone number
            
        Returns:
            Message SID
        """
        # Format message using template
        message = (
            f"Hi {appointment.patient_name}, your {appointment.service} appointment is "
            f"booked for {self._format_date(appointment.date)} at "
            f"{self._format_time(appointment.time)}. Reply CANCEL to reschedule."
        )
        
        # Send message
        return await self.send_sms(phone_number, message)
    
    async def send_booking_alternatives(self, alternatives, service: str, phone_number: str) -> str:
        """
        Send alternative booking slots when requested time is unavailable.
        
        Args:
            alternatives: List of available time slots
            service: Requested service
            phone_number: Recipient phone number
            
        Returns:
            Message SID
        """
        if not alternatives or len(alternatives) == 0:
            message = (
                f"Sorry, we don't have any available slots for {service} in the next few days. "
                f"Please call our office at {self.phone_number} to schedule."
            )
        else:
            alt_times = []
            for i, alt in enumerate(alternatives[:2], 1):
                alt_times.append(f"{i}. {self._format_date(alt.date)} at {self._format_time(alt.time)}")
            
            alt_text = "\n".join(alt_times)
            message = (
                f"Sorry, that time is booked. We have the following slots available for your {service}:\n"
                f"{alt_text}\n"
                f"Reply with the number of your preferred time (e.g., '1' or '2')."
            )
        
        # Send message
        return await self.send_sms(phone_number, message)
    
    async def send_cancellation_confirmation(self, appointment, phone_number: str) -> str:
        """
        Send a cancellation confirmation SMS.
        
        Args:
            appointment: Appointment data
            phone_number: Recipient phone number
            
        Returns:
            Message SID
        """
        message = (
            f"Your {appointment.service} appointment on {self._format_date(appointment.date)} at "
            f"{self._format_time(appointment.time)} has been canceled. "
            f"Reply REBOOK to schedule a new appointment."
        )
        
        # Send message
        return await self.send_sms(phone_number, message)
    
    async def send_reminder(self, appointment, phone_number: str, hours_before: int) -> str:
        """
        Send an appointment reminder SMS.
        
        Args:
            appointment: Appointment data
            phone_number: Recipient phone number
            hours_before: Hours before appointment
            
        Returns:
            Message SID
        """
        time_text = "tomorrow" if hours_before == 24 else f"in {hours_before} hours"
        
        message = (
            f"Reminder: Hi {appointment.patient_name}, your {appointment.service} appointment is "
            f"{time_text} on {self._format_date(appointment.date)} at "
            f"{self._format_time(appointment.time)}. Reply CANCEL to reschedule."
        )
        
        # Send message
        return await self.send_sms(phone_number, message)
    
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
    
    def _format_date(self, date_str: str) -> str:
        """
        Convert YYYY-MM-DD to human-readable format.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Formatted date string
        """
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%A, %B %d, %Y")
    
    def _format_time(self, time_str: str) -> str:
        """
        Convert HH:MM to 12-hour format.
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            Formatted time string
        """
        from datetime import datetime
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%I:%M %p")
