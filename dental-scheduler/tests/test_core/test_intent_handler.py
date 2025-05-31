import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.intent_handler import IntentHandler
from app.models.message import Intent, SMSResponse
from app.models.appointment import Appointment, TimeSlot

@pytest.fixture
def intent_handler():
    """Create an IntentHandler instance with mocked services."""
    calendar_service = MagicMock()
    twilio_service = MagicMock()
    
    return IntentHandler(
        calendar_service=calendar_service,
        twilio_service=twilio_service
    )

@pytest.mark.asyncio
async def test_handle_booking_success(intent_handler):
    """Test handling a successful booking intent."""
    # Arrange
    intent = Intent(
        intent_type="book",
        date="2025-06-10",
        time="14:00",
        service="Cleaning",
        patient_name="John Smith"
    )
    phone_number = "+11234567890"
    
    # Mock calendar service
    intent_handler.calendar_service.check_availability = AsyncMock(return_value=True)
    appointment = Appointment(
        id="test_id",
        service=intent.service,
        patient_name=intent.patient_name,
        phone_number=phone_number,
        date=intent.date,
        time=intent.time,
        end_time="15:00"
    )
    intent_handler.calendar_service.create_appointment = AsyncMock(return_value=appointment)
    
    # Mock twilio service
    intent_handler.twilio_service.send_booking_confirmation = AsyncMock(return_value="msg_sid")
    
    # Act
    result = await intent_handler.handle_booking(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "confirmed" in result.message
    intent_handler.calendar_service.check_availability.assert_called_once_with(intent.date, intent.time)
    intent_handler.calendar_service.create_appointment.assert_called_once()
    intent_handler.twilio_service.send_booking_confirmation.assert_called_once_with(appointment, phone_number)

@pytest.mark.asyncio
async def test_handle_booking_unavailable(intent_handler):
    """Test handling a booking intent when the slot is unavailable."""
    # Arrange
    intent = Intent(
        intent_type="book",
        date="2025-06-10",
        time="14:00",
        service="Cleaning",
        patient_name="John Smith"
    )
    phone_number = "+11234567890"
    
    # Mock calendar service
    intent_handler.calendar_service.check_availability = AsyncMock(return_value=False)
    alternatives = [
        TimeSlot(date="2025-06-10", time="15:00"),
        TimeSlot(date="2025-06-10", time="16:00")
    ]
    intent_handler.calendar_service.find_alternatives = AsyncMock(return_value=alternatives)
    
    # Mock twilio service
    intent_handler.twilio_service.send_booking_alternatives = AsyncMock(return_value="msg_sid")
    
    # Act
    result = await intent_handler.handle_booking(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "not available" in result.message
    intent_handler.calendar_service.check_availability.assert_called_once_with(intent.date, intent.time)
    intent_handler.calendar_service.find_alternatives.assert_called_once_with(intent.date, intent.time)
    intent_handler.twilio_service.send_booking_alternatives.assert_called_once_with(alternatives, intent.service, phone_number)

@pytest.mark.asyncio
async def test_handle_booking_incomplete(intent_handler):
    """Test handling an incomplete booking intent."""
    # Arrange
    intent = Intent(
        intent_type="book",
        date="2025-06-10",
        time="",  # Missing time
        service="Cleaning",
        patient_name="John Smith"
    )
    phone_number = "+11234567890"
    
    # Act
    result = await intent_handler.handle_booking(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "time" in result.message  # Should mention the missing field
    intent_handler.calendar_service.check_availability.assert_not_called()

@pytest.mark.asyncio
async def test_handle_reschedule_success(intent_handler):
    """Test handling a successful reschedule intent."""
    # Arrange
    intent = Intent(
        intent_type="reschedule",
        date="2025-06-11",
        time="15:00",
        service="",
        patient_name=""
    )
    phone_number = "+11234567890"
    
    # Mock calendar service
    existing_appointment = Appointment(
        id="test_id",
        service="Cleaning",
        patient_name="John Smith",
        phone_number=phone_number,
        date="2025-06-10",
        time="14:00",
        end_time="15:00"
    )
    intent_handler.calendar_service.find_appointment_by_phone = AsyncMock(return_value=existing_appointment)
    intent_handler.calendar_service.check_availability = AsyncMock(return_value=True)
    updated_appointment = Appointment(
        id="test_id",
        service="Cleaning",
        patient_name="John Smith",
        phone_number=phone_number,
        date=intent.date,
        time=intent.time,
        end_time="16:00"
    )
    intent_handler.calendar_service.update_appointment = AsyncMock(return_value=updated_appointment)
    
    # Mock twilio service
    intent_handler.twilio_service.send_booking_confirmation = AsyncMock(return_value="msg_sid")
    
    # Act
    result = await intent_handler.handle_reschedule(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "rescheduled" in result.message
    intent_handler.calendar_service.find_appointment_by_phone.assert_called_once_with(phone_number)
    intent_handler.calendar_service.check_availability.assert_called_once_with(intent.date, intent.time)
    intent_handler.calendar_service.update_appointment.assert_called_once_with(
        existing_appointment.id,
        intent.date,
        intent.time
    )
    intent_handler.twilio_service.send_booking_confirmation.assert_called_once_with(updated_appointment, phone_number)

@pytest.mark.asyncio
async def test_handle_reschedule_no_appointment(intent_handler):
    """Test handling a reschedule intent when no appointment exists."""
    # Arrange
    intent = Intent(
        intent_type="reschedule",
        date="2025-06-11",
        time="15:00",
        service="",
        patient_name=""
    )
    phone_number = "+11234567890"
    
    # Mock calendar service
    intent_handler.calendar_service.find_appointment_by_phone = AsyncMock(return_value=None)
    
    # Act
    result = await intent_handler.handle_reschedule(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "couldn't find" in result.message.lower()
    intent_handler.calendar_service.find_appointment_by_phone.assert_called_once_with(phone_number)
    intent_handler.calendar_service.check_availability.assert_not_called()

@pytest.mark.asyncio
async def test_handle_cancellation_success(intent_handler):
    """Test handling a successful cancellation intent."""
    # Arrange
    intent = Intent(
        intent_type="cancel",
        date="",
        time="",
        service="",
        patient_name=""
    )
    phone_number = "+11234567890"
    
    # Mock calendar service
    existing_appointment = Appointment(
        id="test_id",
        service="Cleaning",
        patient_name="John Smith",
        phone_number=phone_number,
        date="2025-06-10",
        time="14:00",
        end_time="15:00"
    )
    intent_handler.calendar_service.find_appointment_by_phone = AsyncMock(return_value=existing_appointment)
    intent_handler.calendar_service.cancel_appointment = AsyncMock(return_value=True)
    
    # Mock twilio service
    intent_handler.twilio_service.send_cancellation_confirmation = AsyncMock(return_value="msg_sid")
    
    # Act
    result = await intent_handler.handle_cancellation(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "canceled" in result.message
    intent_handler.calendar_service.find_appointment_by_phone.assert_called_once_with(phone_number)
    intent_handler.calendar_service.cancel_appointment.assert_called_once_with(existing_appointment.id)
    intent_handler.twilio_service.send_cancellation_confirmation.assert_called_once_with(existing_appointment, phone_number)

@pytest.mark.asyncio
async def test_handle_cancellation_no_appointment(intent_handler):
    """Test handling a cancellation intent when no appointment exists."""
    # Arrange
    intent = Intent(
        intent_type="cancel",
        date="",
        time="",
        service="",
        patient_name=""
    )
    phone_number = "+11234567890"
    
    # Mock calendar service
    intent_handler.calendar_service.find_appointment_by_phone = AsyncMock(return_value=None)
    
    # Act
    result = await intent_handler.handle_cancellation(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "couldn't find" in result.message.lower()
    intent_handler.calendar_service.find_appointment_by_phone.assert_called_once_with(phone_number)
    intent_handler.calendar_service.cancel_appointment.assert_not_called()

@pytest.mark.asyncio
async def test_handle_inquiry(intent_handler):
    """Test handling an inquiry intent."""
    # Arrange
    intent = Intent(
        intent_type="inquiry",
        date="",
        time="",
        service="",
        patient_name=""
    )
    phone_number = "+11234567890"
    
    # Act
    result = await intent_handler.handle_inquiry(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "information" in result.message.lower()
    assert "hours" in result.message.lower()
    assert "services" in result.message.lower()

@pytest.mark.asyncio
async def test_handle_unknown(intent_handler):
    """Test handling an unknown intent."""
    # Arrange
    phone_number = "+11234567890"
    
    # Act
    result = intent_handler.handle_unknown(phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "not sure" in result.message.lower()
    assert "book" in result.message.lower()
    assert "cancel" in result.message.lower()
    assert "reschedule" in result.message.lower()

@pytest.mark.asyncio
async def test_handle_error(intent_handler):
    """Test error handling in the handle method."""
    # Arrange
    intent = Intent(
        intent_type="book",
        date="2025-06-10",
        time="14:00",
        service="Cleaning",
        patient_name="John Smith"
    )
    phone_number = "+11234567890"
    
    # Mock handle_booking to raise an exception
    intent_handler.handle_booking = AsyncMock(side_effect=Exception("Test error"))
    
    # Act
    result = await intent_handler.handle(intent, phone_number)
    
    # Assert
    assert isinstance(result, SMSResponse)
    assert "trouble" in result.message.lower()
    intent_handler.handle_booking.assert_called_once_with(intent, phone_number)
