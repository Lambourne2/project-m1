from app.services.llm_service import LLMService
from app.services.calendar_service import CalendarService
from app.services.twilio_service import TwilioService
from app.services.redis_service import RedisService
from app.core.intent_handler import IntentHandler
from app.models.message import TwilioWebhook, SMSResponse, Intent
import logging

logger = logging.getLogger("app.core.orchestrator")

class Orchestrator:
    """
    Main orchestration layer for the dental appointment scheduling agent.
    
    This class coordinates the workflow between different components:
    - LLM service for intent parsing
    - Calendar service for appointment management
    - Twilio service for SMS communication
    - Redis service for conversation state management
    - Intent handler for business logic
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        calendar_service: CalendarService,
        twilio_service: TwilioService,
        intent_handler: IntentHandler,
        redis_service: RedisService
    ):
        self.llm_service = llm_service
        self.calendar_service = calendar_service
        self.twilio_service = twilio_service
        self.intent_handler = intent_handler
        self.redis_service = redis_service
    
    async def process_message(self, webhook: TwilioWebhook) -> SMSResponse:
        """
        Process an incoming SMS message.
        
        Args:
            webhook: Twilio webhook data
            
        Returns:
            SMS response
        """
        try:
            # Extract message content
            message_text = webhook.Body
            phone_number = webhook.From
            
            logger.info(f"Processing message from {phone_number}: {message_text}")
            
            # Check for conversation context
            context = await self._get_conversation_context(phone_number)
            
            # Check for simple commands
            if message_text.strip().upper() == "CANCEL":
                return await self._handle_cancel_command(phone_number)
            elif message_text.strip().upper() == "REBOOK":
                return await self._handle_rebook_command(phone_number)
            elif message_text.strip().upper() == "STOP":
                return await self._handle_stop_command(phone_number)
            elif message_text.strip().upper() == "HELP":
                return await self._handle_help_command(phone_number)
            
            # Check if this is a response to alternatives
            if context and context.get("awaiting_alternative_selection"):
                return await self._handle_alternative_selection(message_text, phone_number, context)
            
            # Parse intent using LLM
            intent_data = await self.llm_service.parse_intent(message_text)
            
            # Store intent in context
            await self._update_conversation_context(phone_number, {
                "last_intent": intent_data.dict()
            })
            
            # Handle the intent
            response = await self.intent_handler.handle(intent_data, phone_number)
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return SMSResponse(
                message="Sorry, we're having trouble processing your request. Please try again later or call our office directly."
            )
    
    async def _get_conversation_context(self, phone_number: str) -> dict:
        """
        Get conversation context for a phone number.
        
        Args:
            phone_number: Phone number
            
        Returns:
            Conversation context
        """
        try:
            context = await self.redis_service.get(f"context:{phone_number}")
            return context or {}
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return {}
    
    async def _update_conversation_context(self, phone_number: str, data: dict) -> None:
        """
        Update conversation context for a phone number.
        
        Args:
            phone_number: Phone number
            data: Data to update
        """
        try:
            # Get existing context
            context = await self._get_conversation_context(phone_number)
            
            # Update context
            context.update(data)
            
            # Store updated context
            await self.redis_service.set(
                f"context:{phone_number}",
                context,
                expire=3600  # 1 hour expiration
            )
        except Exception as e:
            logger.error(f"Error updating conversation context: {str(e)}")
    
    async def _handle_cancel_command(self, phone_number: str) -> SMSResponse:
        """
        Handle CANCEL command.
        
        Args:
            phone_number: Phone number
            
        Returns:
            SMS response
        """
        # Create cancel intent
        intent = Intent(
            intent_type="cancel",
            date="",
            time="",
            service="",
            patient_name=""
        )
        
        # Handle intent
        return await self.intent_handler.handle(intent, phone_number)
    
    async def _handle_rebook_command(self, phone_number: str) -> SMSResponse:
        """
        Handle REBOOK command.
        
        Args:
            phone_number: Phone number
            
        Returns:
            SMS response
        """
        return SMSResponse(
            message="To book a new appointment, please let us know what service you need and your preferred date and time."
        )
    
    async def _handle_stop_command(self, phone_number: str) -> SMSResponse:
        """
        Handle STOP command.
        
        Args:
            phone_number: Phone number
            
        Returns:
            SMS response
        """
        # Clear conversation context
        await self.redis_service.delete(f"context:{phone_number}")
        
        return SMSResponse(
            message="You have been unsubscribed from all messages. Reply START to re-enable messages."
        )
    
    async def _handle_help_command(self, phone_number: str) -> SMSResponse:
        """
        Handle HELP command.
        
        Args:
            phone_number: Phone number
            
        Returns:
            SMS response
        """
        return SMSResponse(
            message=(
                "Dental Appointment Scheduler Help:\n"
                "- Book: 'I need a cleaning on Monday at 2pm'\n"
                "- Cancel: 'Cancel my appointment' or reply CANCEL\n"
                "- Reschedule: 'Reschedule my appointment to Tuesday at 3pm'\n"
                "- Stop all messages: reply STOP\n"
                "- For assistance, call our office directly."
            )
        )
    
    async def _handle_alternative_selection(self, message_text: str, phone_number: str, context: dict) -> SMSResponse:
        """
        Handle selection of alternative appointment slots.
        
        Args:
            message_text: Message text
            phone_number: Phone number
            context: Conversation context
            
        Returns:
            SMS response
        """
        try:
            # Try to parse selection as a number
            selection = int(message_text.strip())
            
            # Get alternatives from context
            alternatives = context.get("alternatives", [])
            
            # Check if selection is valid
            if selection < 1 or selection > len(alternatives):
                return SMSResponse(
                    message=f"Please select a number between 1 and {len(alternatives)}."
                )
            
            # Get selected alternative
            selected = alternatives[selection - 1]
            
            # Create booking intent
            intent = Intent(
                intent_type="book",
                date=selected["date"],
                time=selected["time"],
                service=context.get("service", ""),
                patient_name=context.get("patient_name", "")
            )
            
            # Clear awaiting_alternative_selection flag
            await self._update_conversation_context(phone_number, {
                "awaiting_alternative_selection": False,
                "alternatives": None
            })
            
            # Handle booking intent
            return await self.intent_handler.handle(intent, phone_number)
        
        except ValueError:
            return SMSResponse(
                message="Please reply with just the number of your preferred time slot (e.g., '1' or '2')."
            )
        except Exception as e:
            logger.error(f"Error handling alternative selection: {str(e)}")
            return SMSResponse(
                message="Sorry, we couldn't process your selection. Please try booking again with your preferred date and time."
            )
