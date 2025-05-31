import httpx
from app.config import settings
from app.models.message import Intent
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("app.services.llm")

class LLMService:
    """
    Service for interacting with the DeepSeek LLM via OpenRouter.
    
    This service handles:
    - Sending prompts to the LLM
    - Parsing responses into structured data
    - Error handling and retries
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        self.api_key = settings.openrouter_api_key
        self.api_url = "https://openrouter.ai/v1/completions"
        self.model = "deepseek/deepseek-r1-0528:free"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def parse_intent(self, message: str) -> Intent:
        """
        Parse a message to extract intent and appointment details.
        
        Args:
            message: User message
            
        Returns:
            Parsed intent
        """
        try:
            # Create system prompt
            system_prompt = """
            You are a professional dental practice AI assistant. When given a patient's raw message, you must extract exactly these five fields in JSON:

            {
              "intent": "<book, reschedule, cancel, inquiry>",
              "date": "YYYY-MM-DD",
              "time": "HH:MM",
              "service": "<string, e.g., Cleaning, Filling, Crown>",
              "patient_name": "<string>"
            }

            If any field is missing, respond with JSON where those fields are empty strings, and do NOT include any extra keys. Do not wrap your JSON in markdown or quotes—only output the raw JSON object.
            """
            
            # Create user prompt
            user_prompt = f"Message: \"{message}\""
            
            # Call OpenRouter API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 200
                    },
                    timeout=30.0
                )
                
                # Check for errors
                response.raise_for_status()
                
                # Parse response
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                
                logger.info(f"LLM response: {content}")
                
                # Parse JSON content
                import json
                intent_data = json.loads(content)
                
                # Convert to Intent object
                return Intent(
                    intent_type=intent_data.get("intent", ""),
                    date=intent_data.get("date", ""),
                    time=intent_data.get("time", ""),
                    service=intent_data.get("service", ""),
                    patient_name=intent_data.get("patient_name", "")
                )
        
        except Exception as e:
            logger.error(f"Error parsing intent: {str(e)}")
            # Return a default intent for error cases
            return Intent(
                intent_type="unknown",
                date="",
                time="",
                service="",
                patient_name=""
            )
