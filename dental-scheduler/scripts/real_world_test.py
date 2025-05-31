#!/usr/bin/env python3
"""
Real-world testing script for the dental appointment scheduling agent.

This script tests the integration with Twilio and Google Calendar
in a real-world environment.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("real_world_test")

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary components
from app.services.twilio_service import TwilioService
from app.services.calendar_service import CalendarService
from app.services.llm_service import LLMService
from app.services.redis_service import RedisService
from app.core.intent_handler import IntentHandler
from app.core.orchestrator import Orchestrator
from app.models.message import TwilioWebhook, Intent
from app.config import settings

async def test_twilio_connection():
    """Test the connection to Twilio."""
    logger.info("Testing Twilio connection...")
    
    try:
        twilio_service = TwilioService()
        test_message = "This is a test message from the dental appointment scheduling agent."
        
        # Use your own phone number for testing
        test_phone = input("Enter your phone number for testing (E.164 format, e.g., +11234567890): ")
        
        # Send a test message
        message_sid = await twilio_service.send_sms(test_phone, test_message)
        
        if message_sid:
            logger.info(f"Successfully sent test message to {test_phone}. Message SID: {message_sid}")
            return True
        else:
            logger.error("Failed to send test message.")
            return False
    
    except Exception as e:
        logger.error(f"Error testing Twilio connection: {str(e)}")
        return False

async def test_calendar_connection():
    """Test the connection to Google Calendar."""
    logger.info("Testing Google Calendar connection...")
    
    try:
        calendar_service = CalendarService()
        
        # Check connection
        is_connected = await calendar_service.check_connection()
        
        if is_connected:
            logger.info("Successfully connected to Google Calendar.")
            
            # Test creating a test appointment
            test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            test_time = "10:00"
            
            # Check if the slot is available
            is_available = await calendar_service.check_availability(test_date, test_time)
            
            if is_available:
                logger.info(f"Time slot {test_date} at {test_time} is available.")
                
                # Create a test appointment
                appointment = await calendar_service.create_appointment(
                    test_date,
                    test_time,
                    "Test Appointment",
                    "Test Patient",
                    "+11234567890"
                )
                
                logger.info(f"Successfully created test appointment: {appointment.id}")
                
                # Cancel the test appointment
                await calendar_service.cancel_appointment(appointment.id)
                logger.info(f"Successfully canceled test appointment: {appointment.id}")
            else:
                logger.info(f"Time slot {test_date} at {test_time} is not available.")
                
                # Find alternatives
                alternatives = await calendar_service.find_alternatives(test_date, test_time)
                logger.info(f"Found {len(alternatives)} alternative slots.")
            
            return True
        else:
            logger.error("Failed to connect to Google Calendar.")
            return False
    
    except Exception as e:
        logger.error(f"Error testing Google Calendar connection: {str(e)}")
        return False

async def test_llm_connection():
    """Test the connection to the LLM service."""
    logger.info("Testing LLM connection...")
    
    try:
        llm_service = LLMService()
        
        # Test parsing a message
        test_message = "I need a cleaning on Monday at 2pm. This is John Smith."
        
        # Parse the message
        intent = await llm_service.parse_intent(test_message)
        
        if intent:
            logger.info(f"Successfully parsed message. Intent: {intent.intent_type}")
            logger.info(f"Date: {intent.date}, Time: {intent.time}")
            logger.info(f"Service: {intent.service}, Patient: {intent.patient_name}")
            return True
        else:
            logger.error("Failed to parse message.")
            return False
    
    except Exception as e:
        logger.error(f"Error testing LLM connection: {str(e)}")
        return False

async def test_redis_connection():
    """Test the connection to Redis."""
    logger.info("Testing Redis connection...")
    
    try:
        redis_service = RedisService()
        
        # Check connection
        is_connected = await redis_service.ping()
        
        if is_connected:
            logger.info("Successfully connected to Redis.")
            
            # Test setting and getting a value
            test_key = "test:key"
            test_value = {"test": "value"}
            
            await redis_service.set(test_key, test_value)
            retrieved_value = await redis_service.get(test_key)
            
            if retrieved_value == test_value:
                logger.info("Successfully set and retrieved value from Redis.")
                
                # Clean up
                await redis_service.delete(test_key)
                logger.info("Successfully deleted test key from Redis.")
                
                return True
            else:
                logger.error("Failed to retrieve correct value from Redis.")
                return False
        else:
            logger.error("Failed to connect to Redis.")
            return False
    
    except Exception as e:
        logger.error(f"Error testing Redis connection: {str(e)}")
        return False

async def test_end_to_end_flow():
    """Test the end-to-end flow of the system."""
    logger.info("Testing end-to-end flow...")
    
    try:
        # Initialize services
        twilio_service = TwilioService()
        calendar_service = CalendarService()
        llm_service = LLMService()
        redis_service = RedisService()
        
        # Initialize intent handler
        intent_handler = IntentHandler(
            calendar_service=calendar_service,
            twilio_service=twilio_service
        )
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            llm_service=llm_service,
            calendar_service=calendar_service,
            twilio_service=twilio_service,
            intent_handler=intent_handler,
            redis_service=redis_service
        )
        
        # Test phone number
        test_phone = input("Enter your phone number for testing (E.164 format, e.g., +11234567890): ")
        
        # Test booking flow
        logger.info("Testing booking flow...")
        
        # Create a test webhook for booking
        booking_webhook = TwilioWebhook(
            MessageSid="test_sid",
            Body="I need a cleaning tomorrow at 2pm. This is John Smith.",
            From=test_phone,
            To=settings.twilio_phone_number
        )
        
        # Process the booking message
        booking_response = await orchestrator.process_message(booking_webhook)
        logger.info(f"Booking response: {booking_response.message}")
        
        # Wait for user to confirm receipt
        input("Press Enter after you've received the booking confirmation message...")
        
        # Test cancellation flow
        logger.info("Testing cancellation flow...")
        
        # Create a test webhook for cancellation
        cancel_webhook = TwilioWebhook(
            MessageSid="test_sid",
            Body="CANCEL",
            From=test_phone,
            To=settings.twilio_phone_number
        )
        
        # Process the cancellation message
        cancel_response = await orchestrator.process_message(cancel_webhook)
        logger.info(f"Cancellation response: {cancel_response.message}")
        
        # Wait for user to confirm receipt
        input("Press Enter after you've received the cancellation confirmation message...")
        
        logger.info("End-to-end flow test completed successfully.")
        return True
    
    except Exception as e:
        logger.error(f"Error testing end-to-end flow: {str(e)}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting real-world tests...")
    
    # Test Twilio connection
    twilio_ok = await test_twilio_connection()
    
    # Test Google Calendar connection
    calendar_ok = await test_calendar_connection()
    
    # Test LLM connection
    llm_ok = await test_llm_connection()
    
    # Test Redis connection
    redis_ok = await test_redis_connection()
    
    # If all connections are OK, test end-to-end flow
    if twilio_ok and calendar_ok and llm_ok and redis_ok:
        logger.info("All connections are OK. Testing end-to-end flow...")
        await test_end_to_end_flow()
    else:
        logger.error("Some connections failed. Skipping end-to-end flow test.")
    
    logger.info("Real-world tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
