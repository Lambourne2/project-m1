from app.models.message import Intent
from app.services.calendar_service import CalendarService
from app.services.twilio_service import TwilioService
from app.models.message import SMSResponse
from app.models.appointment import Appointment
import logging

logger = logging.getLogger("app.core.intent_handler")

class IntentHandler:
    """
    Handler for different types of intents.
    
    This class processes different intents (book, reschedule, cancel, inquiry)
    and coordinates with the calendar and Twilio services to handle them.
    """
    
    def __init__(
        self,
        calendar_service: CalendarService,
        twilio_service: TwilioService
    ):
        self.calendar_service = calendar_service
        self.twilio_service = twilio_service
    
    async def handle(self, intent: Intent, phone_number: str) -> SMSResponse:
        """
        Handle an intent.
        
        Args:
            intent: Intent data
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        try:
            logger.info(f"Handling intent: {intent.intent_type} for {phone_number}")
            
            if intent.intent_type == "book":
                return await self.handle_booking(intent, phone_number)
            elif intent.intent_type == "reschedule":
                return await self.handle_reschedule(intent, phone_number)
            elif intent.intent_type == "cancel":
                return await self.handle_cancellation(intent, phone_number)
            elif intent.intent_type == "inquiry":
                return await self.handle_inquiry(intent, phone_number)
            else:
                return self.handle_unknown(phone_number)
        except Exception as e:
            logger.error(f"Error handling intent: {str(e)}")
            return SMSResponse(
                message="Sorry, we're having trouble processing your request. Please try again later or call our office directly."
            )
    
    async def handle_booking(self, intent: Intent, phone_number: str) -> SMSResponse:
        """
        Handle booking intent.
        
        Args:
            intent: Booking intent
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        # Check if all required fields are present
        if not self._validate_booking_intent(intent):
            return self._create_follow_up_response(intent, phone_number)
        
        # Check availability
        is_available = await self.calendar_service.check_availability(
            intent.date, intent.time
        )
        
        if is_available:
            # Create appointment
            appointment = await self.calendar_service.create_appointment(
                intent.date,
                intent.time,
                intent.service,
                intent.patient_name,
                phone_number
            )
            
            # Send confirmation SMS
            await self.twilio_service.send_booking_confirmation(appointment, phone_number)
            
            # Create confirmation response
            return SMSResponse(
                message=f"Great! Your {intent.service} appointment is confirmed for {intent.date} at {intent.time}. We'll send you a reminder before your appointment. Reply CANCEL to cancel."
            )
        else:
            # Find alternative slots
            alternatives = await self.calendar_service.find_alternatives(
                intent.date, intent.time
            )
            
            # Send alternatives SMS
            await self.twilio_service.send_booking_alternatives(alternatives, intent.service, phone_number)
            
            # Create alternatives response
            return SMSResponse(
                message=f"Sorry, that time is not available. We've sent you some alternative options via SMS."
            )
    
    async def handle_reschedule(self, intent: Intent, phone_number: str) -> SMSResponse:
        """
        Handle reschedule intent.
        
        Args:
            intent: Reschedule intent
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        # Find existing appointment
        appointment = await self.calendar_service.find_appointment_by_phone(phone_number)
        
        if not appointment:
            return SMSResponse(
                message="We couldn't find an existing appointment for you. Would you like to book a new appointment instead?"
            )
        
        # Check if new date/time is provided
        if not intent.date or not intent.time:
            return SMSResponse(
                message=f"We found your {appointment.service} appointment on {appointment.date} at {appointment.time}. What date and time would you like to reschedule to?"
            )
        
        # Check availability for new time
        is_available = await self.calendar_service.check_availability(
            intent.date, intent.time
        )
        
        if is_available:
            # Update appointment
            updated_appointment = await self.calendar_service.update_appointment(
                appointment.id,
                intent.date,
                intent.time
            )
            
            # Send confirmation SMS
            await self.twilio_service.send_booking_confirmation(updated_appointment, phone_number)
            
            # Create confirmation response
            return SMSResponse(
                message=f"Your appointment has been rescheduled to {intent.date} at {intent.time}. We'll send you a reminder before your appointment. Reply CANCEL to cancel."
            )
        else:
            # Find alternative slots
            alternatives = await self.calendar_service.find_alternatives(
                intent.date, intent.time
            )
            
            # Send alternatives SMS
            await self.twilio_service.send_booking_alternatives(alternatives, appointment.service, phone_number)
            
            # Create alternatives response
            return SMSResponse(
                message=f"Sorry, that time is not available. We've sent you some alternative options via SMS."
            )
    
    async def handle_cancellation(self, intent: Intent, phone_number: str) -> SMSResponse:
        """
        Handle cancellation intent.
        
        Args:
            intent: Cancellation intent
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        # Find existing appointment
        appointment = await self.calendar_service.find_appointment_by_phone(phone_number)
        
        if not appointment:
            return SMSResponse(
                message="We couldn't find an existing appointment for you. Would you like to book a new appointment instead?"
            )
        
        # Cancel appointment
        await self.calendar_service.cancel_appointment(appointment.id)
        
        # Send cancellation confirmation SMS
        await self.twilio_service.send_cancellation_confirmation(appointment, phone_number)
        
        # Create cancellation response
        return SMSResponse(
            message=f"Your {appointment.service} appointment on {appointment.date} at {appointment.time} has been canceled. Reply REBOOK to schedule a new appointment."
        )
    
    async def handle_inquiry(self, intent: Intent, phone_number: str) -> SMSResponse:
        """
        Handle inquiry intent.
        
        Args:
            intent: Inquiry intent
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        # For MVP, we'll use a simple response
        return SMSResponse(
            message=(
                "Thank you for your inquiry. Here's some information about our practice:\n"
                "- Hours: Monday-Friday 9am-5pm\n"
                "- Services: Cleanings, Fillings, Crowns, Root Canals\n"
                "- Insurance: We accept most major dental insurance plans\n"
                "- Address: 123 Main St, Salt Lake City, UT 84101\n"
                "To book an appointment, simply text us with your preferred date, time, and service."
            )
        )
    
    def handle_unknown(self, phone_number: str) -> SMSResponse:
        """
        Handle unknown intent.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        return SMSResponse(
            message=(
                "I'm not sure what you're asking for. You can:\n"
                "- Book an appointment: 'I need a cleaning on Monday at 2pm'\n"
                "- Cancel an appointment: 'Cancel my appointment'\n"
                "- Reschedule: 'Reschedule my appointment to Tuesday at 3pm'\n"
                "- Get help: reply HELP\n"
                "- For other inquiries, please call our office directly."
            )
        )
    
    def _validate_booking_intent(self, intent: Intent) -> bool:
        """
        Validate that a booking intent has all required fields.
        
        Args:
            intent: Booking intent
            
        Returns:
            True if valid, False otherwise
        """
        return (
            intent.date and
            intent.time and
            intent.service and
            intent.patient_name
        )
    
    def _create_follow_up_response(self, intent: Intent, phone_number: str) -> SMSResponse:
        """
        Create a follow-up response for incomplete booking intent.
        
        Args:
            intent: Incomplete booking intent
            phone_number: User's phone number
            
        Returns:
            SMS response
        """
        missing = []
        
        if not intent.date:
            missing.append("date")
        if not intent.time:
            missing.append("time")
        if not intent.service:
            missing.append("service")
        if not intent.patient_name:
            missing.append("name")
        
        missing_str = ", ".join(missing)
        
        return SMSResponse(
            message=f"To book your appointment, I need your {missing_str}. Could you please provide that information?"
        )
