# Dental Appointment Scheduling Agent - Documentation

## Overview

The Dental Appointment Scheduling Agent is an AI-powered solution designed to help dental clinics reduce no-show rates, minimize administrative overhead, and improve patient communication. This system allows patients to book, reschedule, and cancel appointments via SMS, with automated reminders to reduce no-shows.

## System Architecture

The system consists of several integrated components:

1. **Twilio SMS Integration**: Handles incoming and outgoing SMS messages
2. **DeepSeek LLM Integration**: Parses natural language messages to extract appointment details
3. **Google Calendar Integration**: Manages appointment scheduling and availability
4. **Business Logic Layer**: Orchestrates the workflow between components
5. **Automated Reminder System**: Sends appointment reminders at scheduled intervals

## Setup and Configuration

### Prerequisites

- Python 3.9 or higher
- Redis server
- Twilio account with SMS-enabled phone number
- Google Cloud account with Calendar API enabled
- OpenRouter API key for DeepSeek LLM access

### Environment Variables

The application requires the following environment variables to be set:

```
# API Settings
PORT=8000
LOG_LEVEL=info

# Twilio Settings
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Google Calendar Settings
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token

# OpenRouter Settings
OPENROUTER_API_KEY=your_openrouter_api_key

# Redis Settings
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Scheduler Settings
REMINDER_CHECK_INTERVAL=3600  # in seconds
```

### Installation

1. Clone the repository
2. Install dependencies using Poetry:
   ```
   poetry install
   ```
3. Create a `.env` file with the required environment variables
4. Start the application:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. Build and start the containers:
   ```
   docker-compose up -d
   ```
2. The application will be available at `http://localhost:8000`

## Component Details

### Twilio SMS Integration

The Twilio integration handles incoming SMS messages from patients and sends outgoing messages for confirmations and reminders.

#### Webhook Endpoint

The system exposes a webhook endpoint at `/api/twilio/sms` that receives incoming SMS messages from Twilio. This endpoint:

1. Validates the Twilio signature to ensure the request is legitimate
2. Extracts the message content and metadata
3. Passes the message to the orchestrator for processing
4. Returns a TwiML response

#### SMS Sending

The `TwilioService` class provides methods for sending various types of SMS messages:

- Booking confirmations
- Appointment reminders
- Cancellation confirmations
- Alternative slot suggestions

### DeepSeek LLM Integration

The LLM integration uses DeepSeek via OpenRouter to parse natural language messages and extract structured appointment data.

#### Intent Parsing

The `LLMService` class sends messages to the DeepSeek model with a carefully crafted prompt to extract:

- Intent type (book, reschedule, cancel, inquiry)
- Date
- Time
- Service
- Patient name

The model returns a JSON response that is parsed into an `Intent` object for further processing.

### Google Calendar Integration

The Calendar integration manages appointments using Google Calendar as the backend.

#### Appointment Management

The `CalendarService` class provides methods for:

- Checking appointment availability
- Creating new appointments
- Updating existing appointments
- Canceling appointments
- Finding alternative time slots
- Retrieving upcoming appointments for reminders

### Business Logic Layer

The business logic layer orchestrates the workflow between the different components.

#### Orchestrator

The `Orchestrator` class:

1. Receives incoming messages from the Twilio webhook
2. Uses the LLM service to parse the intent
3. Manages conversation context using Redis
4. Delegates to the appropriate intent handler
5. Returns the response to be sent via SMS

#### Intent Handler

The `IntentHandler` class processes different types of intents:

- **Booking**: Checks availability, creates appointments, and sends confirmations
- **Rescheduling**: Finds existing appointments and updates them
- **Cancellation**: Cancels existing appointments
- **Inquiry**: Provides information about the dental practice

### Automated Reminder System

The reminder system sends SMS reminders to patients before their appointments.

#### Reminder Scheduler

The `ReminderScheduler` class:

1. Runs as a background task
2. Periodically checks for upcoming appointments
3. Sends reminders at 72 hours, 24 hours, and 2 hours before appointments

**Note**: The reminder scheduler requires a continuously running application. When deploying to production, ensure the application is configured to run as a service or in a container with appropriate restart policies.

## User Flows

### Booking an Appointment

1. Patient sends an SMS: "I need a cleaning next Tuesday at 2pm. This is John Smith."
2. System parses the message to extract intent, date, time, service, and patient name
3. System checks availability in Google Calendar
4. If the slot is available:
   - System creates an appointment in Google Calendar
   - System sends a confirmation SMS
5. If the slot is not available:
   - System finds alternative slots
   - System sends an SMS with alternative options
   - Patient can reply with their preferred alternative

### Rescheduling an Appointment

1. Patient sends an SMS: "I need to reschedule my appointment to Friday at 3pm."
2. System finds the existing appointment
3. System checks availability for the new time
4. If the slot is available:
   - System updates the appointment in Google Calendar
   - System sends a confirmation SMS
5. If the slot is not available:
   - System finds alternative slots
   - System sends an SMS with alternative options

### Canceling an Appointment

1. Patient sends an SMS: "I need to cancel my appointment."
2. System finds the existing appointment
3. System cancels the appointment in Google Calendar
4. System sends a cancellation confirmation SMS

## API Reference

### Twilio Webhook

```
POST /api/twilio/sms
```

Receives incoming SMS messages from Twilio.

**Request Body**:
- `From`: Sender's phone number
- `Body`: Message content
- `MessageSid`: Twilio message ID
- `To`: Recipient's phone number (Twilio number)

**Response**:
- TwiML response with message to be sent back to the patient

### Health Check

```
GET /api/health
```

Checks the health of the application and its dependencies.

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "redis": "up",
    "google_calendar": "up"
  }
}
```

## Troubleshooting

### Common Issues

#### Twilio Webhook Not Receiving Messages

1. Ensure the webhook URL is correctly configured in the Twilio console
2. Check that the Twilio signature validation is working correctly
3. Verify that the Twilio account SID and auth token are correct

#### Google Calendar Integration Issues

1. Ensure the Google Calendar API is enabled in the Google Cloud Console
2. Verify that the OAuth credentials have the correct scopes
3. Check that the refresh token is valid and has not expired

#### LLM Parsing Errors

1. Verify that the OpenRouter API key is correct
2. Check the LLM response format to ensure it matches the expected JSON structure
3. Adjust the system prompt if necessary to improve parsing accuracy

## Future Enhancements

### Six-Month Recall System

A future enhancement could include an automated recall system that:

1. Tracks patients who had routine cleanings
2. Sends an SMS six months after their appointment to schedule a follow-up
3. Manages the booking process for recall appointments

### Web Widget Integration

Another potential enhancement is a web-based chat widget that:

1. Provides the same functionality as the SMS interface
2. Can be embedded on the dental clinic's website
3. Offers a unified conversation history across channels

## Conclusion

The Dental Appointment Scheduling Agent provides a comprehensive solution for dental clinics to manage appointments via SMS. By leveraging AI and automation, it reduces administrative overhead, minimizes no-show rates, and improves patient communication.
