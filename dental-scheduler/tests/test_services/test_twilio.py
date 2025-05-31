import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.twilio_service import TwilioService
from app.models.appointment import Appointment

@pytest.fixture
def twilio_service():
    """Create a TwilioService instance with mocked client."""
    service = TwilioService()
    service.client = MagicMock()
    service.client.messages.create.return_value = MagicMock(sid="test_sid")
    return service

@pytest.mark.asyncio
async def test_send_sms(twilio_service):
    """Test sending an SMS message."""
    # Arrange
    to = "+11234567890"
    body = "Test message"
    
    # Act
    result = await twilio_service.send_sms(to, body)
    
    # Assert
    assert result == "test_sid"
    twilio_service.client.messages.create.assert_called_once_with(
        body=body,
        from_=twilio_service.phone_number,
        to=to
    )

@pytest.mark.asyncio
async def test_send_booking_confirmation(twilio_service):
    """Test sending a booking confirmation SMS."""
    # Arrange
    appointment = Appointment(
        id="test_id",
        service="Cleaning",
        patient_name="John Smith",
        phone_number="+11234567890",
        date="2025-06-10",
        time="14:00",
        end_time="15:00"
    )
    
    # Mock the send_sms method
    twilio_service.send_sms = AsyncMock(return_value="test_sid")
    
    # Act
    result = await twilio_service.send_booking_confirmation(appointment, appointment.phone_number)
    
    # Assert
    assert result == "test_sid"
    assert twilio_service.send_sms.called
    
    # Check that the message contains the appointment details
    call_args = twilio_service.send_sms.call_args[0]
    assert appointment.phone_number == call_args[0]
    assert appointment.patient_name in call_args[1]
    assert appointment.service in call_args[1]
    assert "June 10" in call_args[1]  # Date formatting
    assert "2:00 PM" in call_args[1]  # Time formatting

@pytest.mark.asyncio
async def test_send_booking_alternatives(twilio_service):
    """Test sending alternative booking slots."""
    # Arrange
    from app.models.appointment import TimeSlot
    alternatives = [
        TimeSlot(date="2025-06-10", time="15:00"),
        TimeSlot(date="2025-06-10", time="16:00")
    ]
    service = "Cleaning"
    phone_number = "+11234567890"
    
    # Mock the send_sms method
    twilio_service.send_sms = AsyncMock(return_value="test_sid")
    
    # Act
    result = await twilio_service.send_booking_alternatives(alternatives, service, phone_number)
    
    # Assert
    assert result == "test_sid"
    assert twilio_service.send_sms.called
    
    # Check that the message contains the alternatives
    call_args = twilio_service.send_sms.call_args[0]
    assert phone_number == call_args[0]
    assert service in call_args[1]
    assert "3:00 PM" in call_args[1]  # First alternative
    assert "4:00 PM" in call_args[1]  # Second alternative

@pytest.mark.asyncio
async def test_send_cancellation_confirmation(twilio_service):
    """Test sending a cancellation confirmation SMS."""
    # Arrange
    appointment = Appointment(
        id="test_id",
        service="Cleaning",
        patient_name="John Smith",
        phone_number="+11234567890",
        date="2025-06-10",
        time="14:00",
        end_time="15:00"
    )
    
    # Mock the send_sms method
    twilio_service.send_sms = AsyncMock(return_value="test_sid")
    
    # Act
    result = await twilio_service.send_cancellation_confirmation(appointment, appointment.phone_number)
    
    # Assert
    assert result == "test_sid"
    assert twilio_service.send_sms.called
    
    # Check that the message contains the appointment details
    call_args = twilio_service.send_sms.call_args[0]
    assert appointment.phone_number == call_args[0]
    assert appointment.service in call_args[1]
    assert "canceled" in call_args[1]

@pytest.mark.asyncio
async def test_send_reminder(twilio_service):
    """Test sending a reminder SMS."""
    # Arrange
    appointment = Appointment(
        id="test_id",
        service="Cleaning",
        patient_name="John Smith",
        phone_number="+11234567890",
        date="2025-06-10",
        time="14:00",
        end_time="15:00"
    )
    hours_before = 24
    
    # Mock the send_sms method
    twilio_service.send_sms = AsyncMock(return_value="test_sid")
    
    # Act
    result = await twilio_service.send_reminder(appointment, appointment.phone_number, hours_before)
    
    # Assert
    assert result == "test_sid"
    assert twilio_service.send_sms.called
    
    # Check that the message contains the appointment details
    call_args = twilio_service.send_sms.call_args[0]
    assert appointment.phone_number == call_args[0]
    assert appointment.patient_name in call_args[1]
    assert appointment.service in call_args[1]
    assert "tomorrow" in call_args[1]  # 24 hours before

@pytest.mark.parametrize("phone_number,expected", [
    ("+11234567890", "+11234567890"),  # Already in E.164 format
    ("1234567890", "+11234567890"),    # 10 digits, add +1
    ("11234567890", "+11234567890"),   # 11 digits starting with 1, add +
    ("(123) 456-7890", "+11234567890") # Formatted number
])
def test_normalize_phone_number(twilio_service, phone_number, expected):
    """Test normalizing phone numbers to E.164 format."""
    # Act
    result = twilio_service._normalize_phone_number(phone_number)
    
    # Assert
    assert result == expected

def test_format_date(twilio_service):
    """Test formatting dates for display."""
    # Arrange
    date_str = "2025-06-10"
    
    # Act
    result = twilio_service._format_date(date_str)
    
    # Assert
    assert result == "Tuesday, June 10, 2025"

def test_format_time(twilio_service):
    """Test formatting times for display."""
    # Arrange
    time_str = "14:00"
    
    # Act
    result = twilio_service._format_time(time_str)
    
    # Assert
    assert result == "2:00 PM"
