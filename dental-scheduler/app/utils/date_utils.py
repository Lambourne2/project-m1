from datetime import datetime, timedelta
import logging

logger = logging.getLogger("app.utils.date_utils")

def parse_date(date_str: str) -> str:
    """
    Parse a date string into YYYY-MM-DD format.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Date in YYYY-MM-DD format
    """
    try:
        # Try to parse as ISO format
        date = datetime.fromisoformat(date_str)
        return date.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    try:
        # Try common formats
        formats = [
            "%Y-%m-%d",      # 2025-06-10
            "%m/%d/%Y",      # 06/10/2025
            "%m-%d-%Y",      # 06-10-2025
            "%d/%m/%Y",      # 10/06/2025
            "%B %d, %Y",     # June 10, 2025
            "%b %d, %Y",     # Jun 10, 2025
            "%d %B %Y",      # 10 June 2025
            "%d %b %Y",      # 10 Jun 2025
            "%Y/%m/%d",      # 2025/06/10
        ]
        
        for fmt in formats:
            try:
                date = datetime.strptime(date_str, fmt)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # Try relative dates
        lower_date = date_str.lower()
        today = datetime.now()
        
        if "today" in lower_date:
            return today.strftime("%Y-%m-%d")
        elif "tomorrow" in lower_date:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "monday" in lower_date:
            days_ahead = 7 - today.weekday() if today.weekday() == 0 else (7 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "tuesday" in lower_date:
            days_ahead = 8 - today.weekday() if today.weekday() == 1 else (8 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "wednesday" in lower_date:
            days_ahead = 9 - today.weekday() if today.weekday() == 2 else (9 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "thursday" in lower_date:
            days_ahead = 10 - today.weekday() if today.weekday() == 3 else (10 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "friday" in lower_date:
            days_ahead = 11 - today.weekday() if today.weekday() == 4 else (11 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "saturday" in lower_date:
            days_ahead = 12 - today.weekday() if today.weekday() == 5 else (12 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "next" in lower_date and "sunday" in lower_date:
            days_ahead = 13 - today.weekday() if today.weekday() == 6 else (13 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "monday" in lower_date:
            days_ahead = 0 if today.weekday() == 0 else 7 - today.weekday()
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "tuesday" in lower_date:
            days_ahead = 0 if today.weekday() == 1 else (1 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "wednesday" in lower_date:
            days_ahead = 0 if today.weekday() == 2 else (2 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "thursday" in lower_date:
            days_ahead = 0 if today.weekday() == 3 else (3 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "friday" in lower_date:
            days_ahead = 0 if today.weekday() == 4 else (4 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "saturday" in lower_date:
            days_ahead = 0 if today.weekday() == 5 else (5 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        elif "sunday" in lower_date:
            days_ahead = 0 if today.weekday() == 6 else (6 - today.weekday()) % 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        # If all else fails, return empty string
        return ""
    
    except Exception as e:
        logger.error(f"Error parsing date: {str(e)}")
        return ""

def parse_time(time_str: str) -> str:
    """
    Parse a time string into HH:MM format.
    
    Args:
        time_str: Time string in various formats
        
    Returns:
        Time in HH:MM format
    """
    try:
        # Try to parse as ISO format
        time = datetime.fromisoformat(f"2000-01-01T{time_str}")
        return time.strftime("%H:%M")
    except ValueError:
        pass
    
    try:
        # Try common formats
        formats = [
            "%H:%M",       # 14:30
            "%H:%M:%S",    # 14:30:00
            "%I:%M %p",    # 2:30 PM
            "%I:%M%p",     # 2:30PM
            "%I:%M",       # 2:30 (assumes AM)
            "%I %p",       # 2 PM
            "%I%p",        # 2PM
        ]
        
        for fmt in formats:
            try:
                time = datetime.strptime(time_str, fmt)
                return time.strftime("%H:%M")
            except ValueError:
                continue
        
        # Try to extract time from text
        import re
        
        # Look for patterns like "2:30 PM", "2:30PM", "2 PM", "2PM", "14:30"
        time_pattern = re.compile(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?')
        match = time_pattern.search(time_str)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3).lower() if match.group(3) else None
            
            # Adjust hour for 12-hour format
            if period == "pm" and hour < 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        # If all else fails, return empty string
        return ""
    
    except Exception as e:
        logger.error(f"Error parsing time: {str(e)}")
        return ""

def format_date_for_display(date_str: str) -> str:
    """
    Format a date string for display.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Formatted date string (e.g., "Monday, June 10, 2025")
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%A, %B %d, %Y")
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return date_str

def format_time_for_display(time_str: str) -> str:
    """
    Format a time string for display.
    
    Args:
        time_str: Time in HH:MM format
        
    Returns:
        Formatted time string (e.g., "2:30 PM")
    """
    try:
        time = datetime.strptime(time_str, "%H:%M")
        return time.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
    except Exception as e:
        logger.error(f"Error formatting time: {str(e)}")
        return time_str
