import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.calendar_service import CalendarService
from app.models.appointment import Appointment, TimeSlot

@pytest.fixture
def calendar_service():
    """Create a CalendarService instance with mocked Google API."""
    service = CalendarService()
    service.service = MagicMock()
    return service

@pytest.mark.asyncio
async def test_check_connection(calendar_service):
    """Test checking Google Calendar API connection."""
    # Arrange
    calendar_service.service.calendars().get().execute.return_value = {"id": "primary"}
    
    # Act
    result = await calendar_service.check_connection()
    
    # Assert
    assert result is True
    calendar_service.service.calendars().get.assert_called_once_with(calendarId=calendar_service.calendar_id)

@pytest.mark.asyncio
async def test_check_connection_error(calendar_service):
    """Test handling connection errors."""
    # Arrange
    calendar_service.service.calendars().get().execute.side_effect = Exception("API error")
    
    # Act
    result = await calendar_service.check_connection()
    
    # Assert
    assert result is False

@pytest.mark.asyncio
async def test_check_availability_available(calendar_service):
    """Test checking availability when slot is available."""
    # Arrange
    date = "2025-06-10"
    time = "14:00"
    
    # Mock the events.list method to return no events
    calendar_service.service.events().list().execute.return_value = {"items": []}
    
    # Act
    result = await calendar_service.check_availability(date, time)
    
    # Assert
    assert result is True
    calendar_service.service.events().list.assert_called_once()

@pytest.mark.asyncio
async def test_check_availability_unavailable(calendar_service):
    """Test checking availability when slot is unavailable."""
    # Arrange
    date = "2025-06-10"
    time = "14:00"
    
    # Mock the events.list method to return an event
    calendar_service.service.events().list().execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Existing Appointment",
                "start": {"dateTime": "2025-06-10T14:00:00Z"},
                "end": {"dateTime": "2025-06-10T15:00:00Z"}
            }
        ]
    }
    
    # Act
    result = await calendar_service.check_availability(date, time)
    
    # Assert
    assert result is False
    calendar_service.service.events().list.assert_called_once()

@pytest.mark.asyncio
async def test_create_appointment(calendar_service):
    """Test creating an appointment."""
    # Arrange
    date = "2025-06-10"
    time = "14:00"
    service = "Cleaning"
    patient_name = "John Smith"
    phone_number = "+11234567890"
    
    # Mock the events.insert method
    calendar_service.service.events().insert().execute.return_value = {
        "id": "new_event_id",
        "summary": f"{service} - {patient_name}",
        "description": phone_number,
        "start": {"dateTime": f"{date}T{time}:00Z"},
        "end": {"dateTime": f"{date}T15:00:00Z"}
    }
    
    # Act
    result = await calendar_service.create_appointment(date, time, service, patient_name, phone_number)
    
    # Assert
    assert isinstance(result, Appointment)
    assert result.id == "new_event_id"
    assert result.service == service
    assert result.patient_name == patient_name
    assert result.phone_number == phone_number
    assert result.date == date
    assert result.time == time
    
    # Verify API call
    calendar_service.service.events().insert.assert_called_once()
    call_args = calendar_service.service.events().insert.call_args[1]
    assert call_args["calendarId"] == calendar_service.calendar_id
    
    # Check event body
    event_body = calendar_service.service.events().insert().execute.call_args[0][0]
    assert event_body["summary"] == f"{service} - {patient_name}"
    assert event_body["description"] == phone_number
    assert event_body["start"]["dateTime"].startswith(f"{date}T{time}:00")
    assert event_body["end"]["dateTime"] > event_body["start"]["dateTime"]

@pytest.mark.asyncio
async def test_update_appointment(calendar_service):
    """Test updating an appointment."""
    # Arrange
    appointment_id = "existing_event_id"
    new_date = "2025-06-11"
    new_time = "15:00"
    
    # Mock the events.get method
    calendar_service.service.events().get().execute.return_value = {
        "id": appointment_id,
        "summary": "Cleaning - John Smith",
        "description": "+11234567890",
        "start": {"dateTime": "2025-06-10T14:00:00Z"},
        "end": {"dateTime": "2025-06-10T15:00:00Z"}
    }
    
    # Mock the events.update method
    calendar_service.service.events().update().execute.return_value = {
        "id": appointment_id,
        "summary": "Cleaning - John Smith",
        "description": "+11234567890",
        "start": {"dateTime": f"{new_date}T{new_time}:00Z"},
        "end": {"dateTime": f"{new_date}T16:00:00Z"}
    }
    
    # Act
    result = await calendar_service.update_appointment(appointment_id, new_date, new_time)
    
    # Assert
    assert isinstance(result, Appointment)
    assert result.id == appointment_id
    assert result.service == "Cleaning"
    assert result.patient_name == "John Smith"
    assert result.phone_number == "+11234567890"
    assert result.date == new_date
    assert result.time == new_time
    
    # Verify API calls
    calendar_service.service.events().get.assert_called_once_with(
        calendarId=calendar_service.calendar_id,
        eventId=appointment_id
    )
    calendar_service.service.events().update.assert_called_once()

@pytest.mark.asyncio
async def test_cancel_appointment(calendar_service):
    """Test canceling an appointment."""
    # Arrange
    appointment_id = "existing_event_id"
    
    # Mock the events.delete method
    calendar_service.service.events().delete().execute.return_value = {}
    
    # Act
    result = await calendar_service.cancel_appointment(appointment_id)
    
    # Assert
    assert result is True
    
    # Verify API call
    calendar_service.service.events().delete.assert_called_once_with(
        calendarId=calendar_service.calendar_id,
        eventId=appointment_id
    )

@pytest.mark.asyncio
async def test_find_appointment_by_phone(calendar_service):
    """Test finding an appointment by phone number."""
    # Arrange
    phone_number = "+11234567890"
    
    # Mock the events.list method
    calendar_service.service.events().list().execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Cleaning - John Smith",
                "description": phone_number,
                "start": {"dateTime": "2025-06-10T14:00:00Z"},
                "end": {"dateTime": "2025-06-10T15:00:00Z"}
            },
            {
                "id": "event2",
                "summary": "Filling - Jane Doe",
                "description": "+19876543210",
                "start": {"dateTime": "2025-06-11T10:00:00Z"},
                "end": {"dateTime": "2025-06-11T11:00:00Z"}
            }
        ]
    }
    
    # Act
    result = await calendar_service.find_appointment_by_phone(phone_number)
    
    # Assert
    assert isinstance(result, Appointment)
    assert result.id == "event1"
    assert result.service == "Cleaning"
    assert result.patient_name == "John Smith"
    assert result.phone_number == phone_number
    assert result.date == "2025-06-10"
    assert result.time == "14:00"
    
    # Verify API call
    calendar_service.service.events().list.assert_called_once()

@pytest.mark.asyncio
async def test_find_appointment_by_phone_not_found(calendar_service):
    """Test finding an appointment by phone number when not found."""
    # Arrange
    phone_number = "+11234567890"
    
    # Mock the events.list method to return no matching events
    calendar_service.service.events().list().execute.return_value = {
        "items": [
            {
                "id": "event2",
                "summary": "Filling - Jane Doe",
                "description": "+19876543210",
                "start": {"dateTime": "2025-06-11T10:00:00Z"},
                "end": {"dateTime": "2025-06-11T11:00:00Z"}
            }
        ]
    }
    
    # Act
    result = await calendar_service.find_appointment_by_phone(phone_number)
    
    # Assert
    assert result is None
    
    # Verify API call
    calendar_service.service.events().list.assert_called_once()

@pytest.mark.asyncio
async def test_find_alternatives(calendar_service):
    """Test finding alternative time slots."""
    # Arrange
    date = "2025-06-10"
    requested_time = "14:00"
    
    # Mock the events.list method
    calendar_service.service.events().list().execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Existing Appointment",
                "start": {"dateTime": "2025-06-10T14:00:00Z"},
                "end": {"dateTime": "2025-06-10T15:00:00Z"}
            },
            {
                "id": "event2",
                "summary": "Another Appointment",
                "start": {"dateTime": "2025-06-10T11:00:00Z"},
                "end": {"dateTime": "2025-06-10T12:00:00Z"}
            }
        ]
    }
    
    # Act
    result = await calendar_service.find_alternatives(date, requested_time)
    
    # Assert
    assert isinstance(result, list)
    assert all(isinstance(slot, TimeSlot) for slot in result)
    assert len(result) > 0
    
    # Verify API call
    calendar_service.service.events().list.assert_called_once()

@pytest.mark.asyncio
async def test_get_appointments_for_reminders(calendar_service):
    """Test getting appointments for reminders."""
    # Arrange
    hours_ahead = 24
    
    # Mock the events.list method
    calendar_service.service.events().list().execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Cleaning - John Smith",
                "description": "+11234567890",
                "start": {"dateTime": "2025-06-10T14:00:00Z"},
                "end": {"dateTime": "2025-06-10T15:00:00Z"}
            }
        ]
    }
    
    # Act
    result = await calendar_service.get_appointments_for_reminders(hours_ahead)
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Appointment)
    assert result[0].id == "event1"
    assert result[0].service == "Cleaning"
    assert result[0].patient_name == "John Smith"
    
    # Verify API call
    calendar_service.service.events().list.assert_called_once()

def test_normalize_phone_number(calendar_service):
    """Test normalizing phone numbers."""
    # Test cases
    test_cases = [
        ("+11234567890", "+11234567890"),  # Already in E.164 format
        ("1234567890", "+11234567890"),    # 10 digits, add +1
        ("11234567890", "+11234567890"),   # 11 digits starting with 1, add +
        ("(123) 456-7890", "+11234567890") # Formatted number
    ]
    
    # Test each case
    for input_number, expected in test_cases:
        result = calendar_service._normalize_phone_number(input_number)
        assert result == expected
