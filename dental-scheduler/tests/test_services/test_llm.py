import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from app.services.llm_service import LLMService
from app.models.message import Intent

@pytest.fixture
def llm_service():
    """Create an LLMService instance with mocked API."""
    service = LLMService()
    service.api_key = "test_api_key"
    return service

@pytest.mark.asyncio
async def test_parse_intent_booking(llm_service):
    """Test parsing a booking intent."""
    # Arrange
    message = "I need a cleaning on June 10 at 2pm. This is John Smith."
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intent": "book",
                        "date": "2025-06-10",
                        "time": "14:00",
                        "service": "Cleaning",
                        "patient_name": "John Smith"
                    })
                }
            }
        ]
    }
    
    # Mock the httpx client
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock()
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Act
        result = await llm_service.parse_intent(message)
        
        # Assert
        assert isinstance(result, Intent)
        assert result.intent_type == "book"
        assert result.date == "2025-06-10"
        assert result.time == "14:00"
        assert result.service == "Cleaning"
        assert result.patient_name == "John Smith"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args["headers"]["Authorization"] == f"Bearer {llm_service.api_key}"
        assert call_args["json"]["model"] == llm_service.model
        assert len(call_args["json"]["messages"]) == 2
        assert call_args["json"]["messages"][0]["role"] == "system"
        assert call_args["json"]["messages"][1]["role"] == "user"
        assert message in call_args["json"]["messages"][1]["content"]

@pytest.mark.asyncio
async def test_parse_intent_reschedule(llm_service):
    """Test parsing a reschedule intent."""
    # Arrange
    message = "I need to reschedule my appointment to Friday at 3pm."
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intent": "reschedule",
                        "date": "2025-06-13",
                        "time": "15:00",
                        "service": "",
                        "patient_name": ""
                    })
                }
            }
        ]
    }
    
    # Mock the httpx client
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock()
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Act
        result = await llm_service.parse_intent(message)
        
        # Assert
        assert isinstance(result, Intent)
        assert result.intent_type == "reschedule"
        assert result.date == "2025-06-13"
        assert result.time == "15:00"
        assert result.service == ""
        assert result.patient_name == ""

@pytest.mark.asyncio
async def test_parse_intent_cancel(llm_service):
    """Test parsing a cancel intent."""
    # Arrange
    message = "I need to cancel my appointment."
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intent": "cancel",
                        "date": "",
                        "time": "",
                        "service": "",
                        "patient_name": ""
                    })
                }
            }
        ]
    }
    
    # Mock the httpx client
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock()
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Act
        result = await llm_service.parse_intent(message)
        
        # Assert
        assert isinstance(result, Intent)
        assert result.intent_type == "cancel"
        assert result.date == ""
        assert result.time == ""
        assert result.service == ""
        assert result.patient_name == ""

@pytest.mark.asyncio
async def test_parse_intent_inquiry(llm_service):
    """Test parsing an inquiry intent."""
    # Arrange
    message = "What services do you offer?"
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intent": "inquiry",
                        "date": "",
                        "time": "",
                        "service": "",
                        "patient_name": ""
                    })
                }
            }
        ]
    }
    
    # Mock the httpx client
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock()
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Act
        result = await llm_service.parse_intent(message)
        
        # Assert
        assert isinstance(result, Intent)
        assert result.intent_type == "inquiry"
        assert result.date == ""
        assert result.time == ""
        assert result.service == ""
        assert result.patient_name == ""

@pytest.mark.asyncio
async def test_parse_intent_api_error(llm_service):
    """Test handling API errors."""
    # Arrange
    message = "I need a cleaning."
    
    # Mock the httpx client to raise an exception
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = Exception("API error")
        
        # Act
        result = await llm_service.parse_intent(message)
        
        # Assert
        assert isinstance(result, Intent)
        assert result.intent_type == "unknown"
        assert result.date == ""
        assert result.time == ""
        assert result.service == ""
        assert result.patient_name == ""

@pytest.mark.asyncio
async def test_parse_intent_invalid_json(llm_service):
    """Test handling invalid JSON responses."""
    # Arrange
    message = "I need a cleaning."
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "This is not valid JSON"
                }
            }
        ]
    }
    
    # Mock the httpx client
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock()
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Act
        result = await llm_service.parse_intent(message)
        
        # Assert
        assert isinstance(result, Intent)
        assert result.intent_type == "unknown"
        assert result.date == ""
        assert result.time == ""
        assert result.service == ""
        assert result.patient_name == ""
