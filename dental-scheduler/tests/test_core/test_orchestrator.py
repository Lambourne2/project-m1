import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.orchestrator import Orchestrator
from app.models.message import TwilioWebhook, SMSResponse, Intent

@pytest.fixture
def orchestrator():
    """Create an Orchestrator instance with mocked services."""
    llm_service = MagicMock()
    calendar_service = MagicMock()
    twilio_service = MagicMock()
    intent_handler = MagicMock()
    redis_service = MagicMock()
    
    return Orchestrator(
        llm_service=llm_service,
        calendar_service=calendar_service,
        twilio_service=twilio_service,
        intent_handler=intent_handler,
        redis_service=redis_service
    )

@pytest.mark.asyncio
async def test_process_message_booking(orchestrator):
    """Test processing a booking message."""
    # Arrange
    webhook = TwilioWebhook(
        MessageSid="test_sid",
        Body="I need a cleaning on Monday at 2pm. This is John Smith.",
        From="+11234567890",
        To="+19876543210"
    )
    
    # Mock the LLM service
    intent = Intent(
        intent_type="book",
        date="2025-06-10",
        time="14:00",
        service="Cleaning",
        patient_name="John Smith"
    )
    orchestrator.llm_service.parse_intent = AsyncMock(return_value=intent)
    
    # Mock the Redis service
    orchestrator._get_conversation_context = AsyncMock(return_value={})
    orchestrator._update_conversation_context = AsyncMock()
    
    # Mock the intent handler
    expected_response = SMSResponse(message="Appointment confirmed")
    orchestrator.intent_handler.handle = AsyncMock(return_value=expected_response)
    
    # Act
    result = await orchestrator.process_message(webhook)
    
    # Assert
    assert result == expected_response
    orchestrator.llm_service.parse_intent.assert_called_once_with(webhook.Body)
    orchestrator.intent_handler.handle.assert_called_once_with(intent, webhook.From)

@pytest.mark.asyncio
async def test_process_message_cancel_command(orchestrator):
    """Test processing a CANCEL command."""
    # Arrange
    webhook = TwilioWebhook(
        MessageSid="test_sid",
        Body="CANCEL",
        From="+11234567890",
        To="+19876543210"
    )
    
    # Mock the Redis service
    orchestrator._get_conversation_context = AsyncMock(return_value={})
    
    # Mock the _handle_cancel_command method
    expected_response = SMSResponse(message="Appointment canceled")
    orchestrator._handle_cancel_command = AsyncMock(return_value=expected_response)
    
    # Act
    result = await orchestrator.process_message(webhook)
    
    # Assert
    assert result == expected_response
    orchestrator._handle_cancel_command.assert_called_once_with(webhook.From)
    orchestrator.llm_service.parse_intent.assert_not_called()

@pytest.mark.asyncio
async def test_process_message_rebook_command(orchestrator):
    """Test processing a REBOOK command."""
    # Arrange
    webhook = TwilioWebhook(
        MessageSid="test_sid",
        Body="REBOOK",
        From="+11234567890",
        To="+19876543210"
    )
    
    # Mock the Redis service
    orchestrator._get_conversation_context = AsyncMock(return_value={})
    
    # Mock the _handle_rebook_command method
    expected_response = SMSResponse(message="Please provide details for your new appointment")
    orchestrator._handle_rebook_command = AsyncMock(return_value=expected_response)
    
    # Act
    result = await orchestrator.process_message(webhook)
    
    # Assert
    assert result == expected_response
    orchestrator._handle_rebook_command.assert_called_once_with(webhook.From)
    orchestrator.llm_service.parse_intent.assert_not_called()

@pytest.mark.asyncio
async def test_process_message_alternative_selection(orchestrator):
    """Test processing a response to alternative slots."""
    # Arrange
    webhook = TwilioWebhook(
        MessageSid="test_sid",
        Body="1",
        From="+11234567890",
        To="+19876543210"
    )
    
    # Mock the Redis service with context indicating awaiting alternative selection
    context = {
        "awaiting_alternative_selection": True,
        "alternatives": [
            {"date": "2025-06-10", "time": "15:00"},
            {"date": "2025-06-10", "time": "16:00"}
        ],
        "service": "Cleaning",
        "patient_name": "John Smith"
    }
    orchestrator._get_conversation_context = AsyncMock(return_value=context)
    
    # Mock the _handle_alternative_selection method
    expected_response = SMSResponse(message="Alternative slot booked")
    orchestrator._handle_alternative_selection = AsyncMock(return_value=expected_response)
    
    # Act
    result = await orchestrator.process_message(webhook)
    
    # Assert
    assert result == expected_response
    orchestrator._handle_alternative_selection.assert_called_once_with(webhook.Body, webhook.From, context)
    orchestrator.llm_service.parse_intent.assert_not_called()

@pytest.mark.asyncio
async def test_process_message_error_handling(orchestrator):
    """Test error handling in process_message."""
    # Arrange
    webhook = TwilioWebhook(
        MessageSid="test_sid",
        Body="I need a cleaning",
        From="+11234567890",
        To="+19876543210"
    )
    
    # Mock the LLM service to raise an exception
    orchestrator.llm_service.parse_intent = AsyncMock(side_effect=Exception("Test error"))
    
    # Mock the Redis service
    orchestrator._get_conversation_context = AsyncMock(return_value={})
    
    # Act
    result = await orchestrator.process_message(webhook)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "trouble" in result.message.lower()
    orchestrator.llm_service.parse_intent.assert_called_once_with(webhook.Body)

@pytest.mark.asyncio
async def test_get_conversation_context(orchestrator):
    """Test getting conversation context."""
    # Arrange
    phone_number = "+11234567890"
    expected_context = {"last_intent": {"intent_type": "book"}}
    orchestrator.redis_service.get = AsyncMock(return_value=expected_context)
    
    # Act
    result = await orchestrator._get_conversation_context(phone_number)
    
    # Assert
    assert result == expected_context
    orchestrator.redis_service.get.assert_called_once_with(f"context:{phone_number}")

@pytest.mark.asyncio
async def test_get_conversation_context_empty(orchestrator):
    """Test getting conversation context when none exists."""
    # Arrange
    phone_number = "+11234567890"
    orchestrator.redis_service.get = AsyncMock(return_value=None)
    
    # Act
    result = await orchestrator._get_conversation_context(phone_number)
    
    # Assert
    assert result == {}
    orchestrator.redis_service.get.assert_called_once_with(f"context:{phone_number}")

@pytest.mark.asyncio
async def test_update_conversation_context(orchestrator):
    """Test updating conversation context."""
    # Arrange
    phone_number = "+11234567890"
    existing_context = {"last_intent": {"intent_type": "book"}}
    new_data = {"awaiting_alternative_selection": True}
    
    orchestrator._get_conversation_context = AsyncMock(return_value=existing_context)
    orchestrator.redis_service.set = AsyncMock(return_value=True)
    
    # Act
    await orchestrator._update_conversation_context(phone_number, new_data)
    
    # Assert
    expected_context = {**existing_context, **new_data}
    orchestrator._get_conversation_context.assert_called_once_with(phone_number)
    orchestrator.redis_service.set.assert_called_once_with(
        f"context:{phone_number}",
        expected_context,
        expire=3600
    )

@pytest.mark.asyncio
async def test_handle_cancel_command(orchestrator):
    """Test handling CANCEL command."""
    # Arrange
    phone_number = "+11234567890"
    expected_response = SMSResponse(message="Appointment canceled")
    orchestrator.intent_handler.handle = AsyncMock(return_value=expected_response)
    
    # Act
    result = await orchestrator._handle_cancel_command(phone_number)
    
    # Assert
    assert result == expected_response
    orchestrator.intent_handler.handle.assert_called_once()
    call_args = orchestrator.intent_handler.handle.call_args[0]
    assert call_args[0].intent_type == "cancel"
    assert call_args[1] == phone_number

@pytest.mark.asyncio
async def test_handle_alternative_selection_valid(orchestrator):
    """Test handling valid alternative selection."""
    # Arrange
    message_text = "1"
    phone_number = "+11234567890"
    context = {
        "alternatives": [
            {"date": "2025-06-10", "time": "15:00"},
            {"date": "2025-06-10", "time": "16:00"}
        ],
        "service": "Cleaning",
        "patient_name": "John Smith"
    }
    
    expected_response = SMSResponse(message="Appointment booked")
    orchestrator.intent_handler.handle = AsyncMock(return_value=expected_response)
    orchestrator._update_conversation_context = AsyncMock()
    
    # Act
    result = await orchestrator._handle_alternative_selection(message_text, phone_number, context)
    
    # Assert
    assert result == expected_response
    orchestrator.intent_handler.handle.assert_called_once()
    orchestrator._update_conversation_context.assert_called_once()
    
    # Check that the correct intent was created
    call_args = orchestrator.intent_handler.handle.call_args[0]
    assert call_args[0].intent_type == "book"
    assert call_args[0].date == "2025-06-10"
    assert call_args[0].time == "15:00"
    assert call_args[0].service == "Cleaning"
    assert call_args[0].patient_name == "John Smith"

@pytest.mark.asyncio
async def test_handle_alternative_selection_invalid(orchestrator):
    """Test handling invalid alternative selection."""
    # Arrange
    message_text = "3"  # Out of range
    phone_number = "+11234567890"
    context = {
        "alternatives": [
            {"date": "2025-06-10", "time": "15:00"},
            {"date": "2025-06-10", "time": "16:00"}
        ],
        "service": "Cleaning",
        "patient_name": "John Smith"
    }
    
    # Act
    result = await orchestrator._handle_alternative_selection(message_text, phone_number, context)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "select a number between" in result.message.lower()
    orchestrator.intent_handler.handle.assert_not_called()

@pytest.mark.asyncio
async def test_handle_alternative_selection_non_numeric(orchestrator):
    """Test handling non-numeric alternative selection."""
    # Arrange
    message_text = "first one"  # Not a number
    phone_number = "+11234567890"
    context = {
        "alternatives": [
            {"date": "2025-06-10", "time": "15:00"},
            {"date": "2025-06-10", "time": "16:00"}
        ],
        "service": "Cleaning",
        "patient_name": "John Smith"
    }
    
    # Act
    result = await orchestrator._handle_alternative_selection(message_text, phone_number, context)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "reply with just the number" in result.message.lower()
    orchestrator.intent_handler.handle.assert_not_called()
