#!/usr/bin/env python3
"""
Edge case and error handling test script for the dental appointment scheduling agent.

This script tests various edge cases and error scenarios to ensure
the system is robust and handles errors gracefully.
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
logger = logging.getLogger("edge_case_test")

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

async def test_invalid_date_time_formats():
    """Test handling of invalid date and time formats."""
    logger.info("Testing invalid date and time formats...")
    
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
        
        # Test cases with invalid date/time formats
        test_cases = [
            "I need a cleaning on the 32nd of June at 2pm",
            "I need a cleaning tomorrow at 25:00",
            "I need a cleaning yesterday at 2pm",
            "I need a cleaning on 2025-13-45 at 2pm",
            "I need a cleaning on Monday at midnight"
        ]
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"Testing case {i+1}: {test_case}")
            
            # Create a test webhook
            webhook = TwilioWebhook(
                MessageSid=f"test_sid_{i}",
                Body=test_case,
                From="+11234567890",
                To=settings.twilio_phone_number
            )
            
            # Process the message
            response = await orchestrator.process_message(webhook)
            logger.info(f"Response: {response.message}")
            
            # Check if the response is appropriate
            if "trouble" in response.message.lower() or "provide" in response.message.lower():
                logger.info("System correctly handled invalid date/time format.")
            else:
                logger.warning("System may not have properly handled invalid date/time format.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing invalid date/time formats: {str(e)}")
        return False

async def test_service_unavailability():
    """Test handling of service unavailability."""
    logger.info("Testing service unavailability...")
    
    try:
        # Initialize services with invalid credentials
        
        # Test Twilio service unavailability
        logger.info("Testing Twilio service unavailability...")
        
        # Create a Twilio service with invalid credentials
        invalid_twilio = TwilioService()
        invalid_twilio.account_sid = "invalid_sid"
        invalid_twilio.auth_token = "invalid_token"
        
        try:
            # Try to send an SMS
            await invalid_twilio.send_sms("+11234567890", "Test message")
            logger.warning("Expected Twilio service to fail, but it didn't.")
        except Exception as e:
            logger.info(f"Twilio service correctly failed: {str(e)}")
        
        # Test LLM service unavailability
        logger.info("Testing LLM service unavailability...")
        
        # Create an LLM service with invalid API key
        invalid_llm = LLMService()
        invalid_llm.api_key = "invalid_key"
        
        # Try to parse a message
        intent = await invalid_llm.parse_intent("I need a cleaning tomorrow at 2pm")
        
        # Check if the service gracefully handled the error
        if intent and intent.intent_type == "unknown":
            logger.info("LLM service correctly handled API failure.")
        else:
            logger.warning("LLM service may not have properly handled API failure.")
        
        # Test Redis service unavailability
        logger.info("Testing Redis service unavailability...")
        
        # Create a Redis service with invalid connection details
        invalid_redis = RedisService()
        invalid_redis.redis_url = "redis://invalid-host:6379/0"
        
        # Try to ping Redis
        is_connected = await invalid_redis.ping()
        
        if not is_connected:
            logger.info("Redis service correctly handled connection failure.")
        else:
            logger.warning("Redis service may not have properly handled connection failure.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing service unavailability: {str(e)}")
        return False

async def test_concurrent_requests():
    """Test handling of concurrent requests."""
    logger.info("Testing concurrent requests...")
    
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
        
        # Create test webhooks
        webhooks = [
            TwilioWebhook(
                MessageSid=f"test_sid_{i}",
                Body=f"I need a cleaning on {(datetime.now() + timedelta(days=i+1)).strftime('%A')} at 2pm. This is Patient {i}.",
                From=f"+1123456789{i}",
                To=settings.twilio_phone_number
            )
            for i in range(5)
        ]
        
        # Process messages concurrently
        logger.info("Processing 5 messages concurrently...")
        tasks = [orchestrator.process_message(webhook) for webhook in webhooks]
        responses = await asyncio.gather(*tasks)
        
        # Check responses
        for i, response in enumerate(responses):
            logger.info(f"Response {i+1}: {response.message}")
        
        logger.info("Successfully processed concurrent requests.")
        return True
    
    except Exception as e:
        logger.error(f"Error testing concurrent requests: {str(e)}")
        return False

async def test_malformed_messages():
    """Test handling of malformed or unexpected messages."""
    logger.info("Testing malformed messages...")
    
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
        
        # Test cases with malformed or unexpected messages
        test_cases = [
            "",  # Empty message
            "?",  # Single character
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit...",  # Random text
            "😀 🦷 🦷 😀",  # Emojis
            "SELECT * FROM appointments;",  # SQL injection attempt
            "<script>alert('XSS')</script>",  # XSS attempt
            "I need a cleaning\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",  # Excessive newlines
            "a" * 1000  # Very long message
        ]
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"Testing case {i+1}: {test_case[:30]}...")
            
            # Create a test webhook
            webhook = TwilioWebhook(
                MessageSid=f"test_sid_{i}",
                Body=test_case,
                From="+11234567890",
                To=settings.twilio_phone_number
            )
            
            # Process the message
            response = await orchestrator.process_message(webhook)
            logger.info(f"Response: {response.message}")
            
            # Check if the system didn't crash
            if response:
                logger.info("System handled malformed message without crashing.")
            else:
                logger.warning("System may have issues with malformed messages.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing malformed messages: {str(e)}")
        return False

async def test_rate_limiting():
    """Test handling of rate limiting."""
    logger.info("Testing rate limiting...")
    
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
        
        # Send many requests in quick succession to test rate limiting
        logger.info("Sending 10 requests in quick succession...")
        
        webhook = TwilioWebhook(
            MessageSid="test_sid",
            Body="I need a cleaning tomorrow at 2pm. This is John Smith.",
            From="+11234567890",
            To=settings.twilio_phone_number
        )
        
        responses = []
        for i in range(10):
            response = await orchestrator.process_message(webhook)
            responses.append(response)
            logger.info(f"Response {i+1}: {response.message}")
        
        # Check if all requests were processed
        if all(responses):
            logger.info("All requests were processed successfully.")
        else:
            logger.warning("Some requests may have been rate limited.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing rate limiting: {str(e)}")
        return False

async def main():
    """Run all edge case and error handling tests."""
    logger.info("Starting edge case and error handling tests...")
    
    # Test invalid date and time formats
    await test_invalid_date_time_formats()
    
    # Test service unavailability
    await test_service_unavailability()
    
    # Test concurrent requests
    await test_concurrent_requests()
    
    # Test malformed messages
    await test_malformed_messages()
    
    # Test rate limiting
    await test_rate_limiting()
    
    logger.info("Edge case and error handling tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
