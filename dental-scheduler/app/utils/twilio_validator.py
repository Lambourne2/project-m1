from twilio.request_validator import RequestValidator
from fastapi import Request, HTTPException, Depends
from app.config import settings
import logging

logger = logging.getLogger("app.utils.twilio_validator")

class TwilioWebhookValidator:
    """
    Utility class for validating Twilio webhook requests.
    
    This ensures that webhook requests are actually coming from Twilio
    and not from a malicious source.
    """
    
    def __init__(self):
        self.validator = RequestValidator(settings.twilio_auth_token)
    
    async def validate_request(self, request: Request) -> bool:
        """
        Validate that the request is coming from Twilio.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            True if the request is valid, False otherwise
        """
        # Get the Twilio signature from the request headers
        twilio_signature = request.headers.get("X-Twilio-Signature", "")
        
        # Get the full URL of the request
        url = str(request.url)
        
        # Get the request body as form data
        form_data = await request.form()
        
        # Convert form data to dict
        form_dict = dict(form_data)
        
        # Validate the request
        is_valid = self.validator.validate(
            url,
            form_dict,
            twilio_signature
        )
        
        if not is_valid:
            logger.warning(f"Invalid Twilio webhook request: {url}")
        
        return is_valid

# Create a dependency for validating Twilio webhook requests
async def validate_twilio_request(request: Request):
    validator = TwilioWebhookValidator()
    if not await validator.validate_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    return True
