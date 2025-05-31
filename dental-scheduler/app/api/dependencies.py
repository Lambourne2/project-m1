from app.services.llm_service import LLMService
from app.services.calendar_service import CalendarService
from app.services.twilio_service import TwilioService
from app.services.redis_service import RedisService
from app.core.intent_handler import IntentHandler
from app.core.orchestrator import Orchestrator

# Service dependencies
def get_llm_service():
    return LLMService()

def get_calendar_service():
    return CalendarService()

def get_twilio_service():
    return TwilioService()

def get_redis_service():
    return RedisService()

# Handler dependencies
def get_intent_handler(
    calendar_service: CalendarService = Depends(get_calendar_service),
    twilio_service: TwilioService = Depends(get_twilio_service)
):
    return IntentHandler(calendar_service, twilio_service)

# Orchestrator dependency
def get_orchestrator(
    llm_service: LLMService = Depends(get_llm_service),
    calendar_service: CalendarService = Depends(get_calendar_service),
    twilio_service: TwilioService = Depends(get_twilio_service),
    intent_handler: IntentHandler = Depends(get_intent_handler),
    redis_service: RedisService = Depends(get_redis_service)
):
    return Orchestrator(
        llm_service=llm_service,
        calendar_service=calendar_service,
        twilio_service=twilio_service,
        intent_handler=intent_handler,
        redis_service=redis_service
    )
