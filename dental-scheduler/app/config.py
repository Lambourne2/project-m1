from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    # API settings
    api_title: str = "Dental Appointment Scheduler"
    api_description: str = "AI-powered dental appointment scheduling agent"
    api_version: str = "0.1.0"
    port: int = Field(8000, env="PORT")
    log_level: str = Field("info", env="LOG_LEVEL")
    
    # Twilio settings
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., env="TWILIO_PHONE_NUMBER")
    
    # Google Calendar settings
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_refresh_token: str = Field(..., env="GOOGLE_REFRESH_TOKEN")
    
    # OpenRouter settings
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    
    # Redis settings
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # Scheduler settings
    reminder_check_interval: int = Field(3600, env="REMINDER_CHECK_INTERVAL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()
