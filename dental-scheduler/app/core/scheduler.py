import asyncio
from datetime import datetime, timedelta
from app.services.calendar_service import CalendarService
from app.services.twilio_service import TwilioService
import logging

logger = logging.getLogger("app.core.scheduler")

class ReminderScheduler:
    """
    Scheduler for sending appointment reminders.
    
    This class handles:
    - Scheduling reminders for upcoming appointments
    - Sending reminders at appropriate times (72h, 24h, 2h before)
    - Managing the background task for periodic checks
    """
    
    def __init__(
        self,
        calendar_service: CalendarService,
        twilio_service: TwilioService
    ):
        """Initialize the reminder scheduler."""
        self.calendar_service = calendar_service
        self.twilio_service = twilio_service
        self.running = False
        self.task = None
        self.check_interval = 3600  # 1 hour in seconds
    
    async def start(self):
        """Start the reminder scheduler."""
        if self.running:
            return
        
        logger.info("Starting reminder scheduler")
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
    
    async def stop(self):
        """Stop the reminder scheduler."""
        if not self.running:
            return
        
        logger.info("Stopping reminder scheduler")
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            try:
                # Process reminders
                await self._process_reminders()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                
                # Wait before retry
                await asyncio.sleep(300)  # 5 minutes
    
    async def _process_reminders(self):
        """Process reminders for upcoming appointments."""
        logger.info("Processing reminders")
        
        try:
            # Check for appointments in exactly 72 hours
            await self._send_reminders_for_time_window(72)
            
            # Check for appointments in exactly 24 hours
            await self._send_reminders_for_time_window(24)
            
            # Check for appointments in exactly 2 hours
            await self._send_reminders_for_time_window(2)
        except Exception as e:
            logger.error(f"Error processing reminders: {e}")
    
    async def _send_reminders_for_time_window(self, hours_ahead: int):
        """
        Send reminders for appointments in the specified time window.
        
        Args:
            hours_ahead: Hours ahead to look for appointments
        """
        try:
            # Get appointments in time window
            appointments = await self.calendar_service.get_appointments_for_reminders(hours_ahead)
            
            logger.info(f"Found {len(appointments)} appointments {hours_ahead} hours ahead")
            
            # Send reminders
            for appointment in appointments:
                if not appointment.phone_number:
                    logger.warning(f"No phone number for appointment {appointment.id}")
                    continue
                
                try:
                    await self.twilio_service.send_reminder(
                        appointment, appointment.phone_number, hours_ahead
                    )
                    logger.info(f"Sent {hours_ahead}-hour reminder for appointment {appointment.id}")
                except Exception as e:
                    logger.error(f"Error sending reminder for appointment {appointment.id}: {e}")
        
        except Exception as e:
            logger.error(f"Error sending reminders for {hours_ahead} hours ahead: {e}")
