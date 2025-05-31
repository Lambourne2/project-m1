from fastapi import APIRouter, Request, Depends, HTTPException, Response
from app.core.orchestrator import Orchestrator
from app.models.message import TwilioWebhook, SMSResponse
from app.services.twilio_service import TwilioService
from app.api.dependencies import get_orchestrator
from twilio.twiml.messaging_response import MessagingResponse
import logging

router = APIRouter()
logger = logging.getLogger("app.api.twilio")

@router.post("/sms")
async def handle_sms(
    request: Request,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Handle incoming SMS messages from Twilio.
    
    This endpoint receives webhook requests from Twilio when a new SMS message
    is received. It extracts the message content, processes it through the
    orchestrator, and returns a TwiML response.
    """
    try:
        # Parse form data from Twilio webhook
        form_data = await request.form()
        
        # Extract message data
        webhook_data = TwilioWebhook(
            MessageSid=form_data.get("MessageSid", ""),
            Body=form_data.get("Body", ""),
            From=form_data.get("From", ""),
            To=form_data.get("To", "")
        )
        
        logger.info(f"Received SMS from {webhook_data.From}: {webhook_data.Body}")
        
        # Process message through orchestrator
        response = await orchestrator.process_message(webhook_data)
        
        # Create TwiML response
        twiml_response = MessagingResponse()
        if response.message:
            twiml_response.message(response.message)
        
        return Response(
            content=str(twiml_response),
            media_type="application/xml"
        )
    
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {str(e)}")
        # Return empty TwiML response to avoid Twilio errors
        twiml_response = MessagingResponse()
        return Response(
            content=str(twiml_response),
            media_type="application/xml"
        )
