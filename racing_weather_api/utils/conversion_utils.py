"""
Utility functions for handling units conversion and data formatting.
"""
import logging
import pytz
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    if celsius == 'N/A' or celsius is None:
        return 'N/A'
    try:
        return round((celsius * 9 / 5) + 32, 1)
    except (TypeError, ValueError):
        return 'N/A'


def kph_to_mph(kph):
    """Convert kilometers per hour to miles per hour."""
    if kph == 'N/A' or kph is None:
        return 'N/A'
    try:
        return round(kph * 0.621371, 1)
    except (TypeError, ValueError):
        return 'N/A'


def convert_est_to_utc(event_date_str: str, event_time_str: str):
    """Convert EST event time to UTC datetime."""
    try:
        # Parse event date and time
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        event_time = datetime.strptime(event_time_str, '%I:%M %p')
        event_datetime = event_date.replace(hour=event_time.hour, minute=event_time.minute)
        
        # Create timezone objects
        est = pytz.timezone('US/Eastern')
        utc = pytz.UTC
        
        # Localize to EST and convert to UTC
        event_datetime_est = est.localize(event_datetime)
        event_datetime_utc = event_datetime_est.astimezone(utc)
        
        # Return as naive datetime for comparison
        return event_datetime_utc.replace(tzinfo=None)
        
    except Exception as e:
        logger.error(f"Error converting EST to UTC: {e}")
        return None


def convert_utc_to_est(utc_datetime):
    """Convert UTC datetime back to EST for display."""
    try:
        # Create timezone objects
        utc = pytz.UTC
        est = pytz.timezone('US/Eastern')
        
        # Add UTC timezone and convert to EST
        utc_datetime_tz = utc.localize(utc_datetime)
        est_datetime = utc_datetime_tz.astimezone(est)
        
        # Return as naive datetime
        return est_datetime.replace(tzinfo=None)
        
    except Exception as e:
        logger.error(f"Error converting UTC to EST: {e}")
        return utc_datetime  # Return ori
    

def parse_event_time(event_time_str: str):
    """Parse event time string into a standardized format."""
    event_time_str = event_time_str.strip().lower()
    if ':' not in event_time_str:
        event_time_str = event_time_str.replace(' am', ':00 AM').replace(' pm', ':00 PM')
    else:
        event_time_str = event_time_str.upper()

    return event_time_str



def parse_datetime(date_str, time_str):
    """Turn event date and time e.g. 2PM into single datatime value"""
    dt_str = f"{date_str} {time_str}"
    formats = ["%Y-%m-%d %I %p", "%Y-%m-%d %I:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date/time format not recognized: {dt_str}")


def normalize_text_case(data):
    """Normalize text case in JSON structure, preserve known acronyms in uppercase"""
    
    skip_keys = {"time", "channel", "track_location"}
    known_acronyms = {"NASCAR", "CARS", "ARCA", "PLM"}  # add more acronyms here as needed
    
    def normalize_string(s):
        if s.strip().upper() == "INDYCAR SERIES":
            return "IndyCar Series"
        
        words = s.split()
        normalized_words = []
        for word in words:
            if word.upper() in known_acronyms:
                normalized_words.append(word.upper())
            else:
                normalized_words.append(word.title())
        return " ".join(normalized_words)
    
    if isinstance(data, dict):
        return {
            key: value if key in skip_keys else normalize_text_case(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [normalize_text_case(item) for item in data]
    elif isinstance(data, str):
        return normalize_string(data)
    else:
        return data  # Leave numbers, bools, None unchanged


def convert_wind_direction(direction):
    """Convert wind text e.g. North to N, North_Northwest to N NW"""
    if not isinstance(direction, str):
        return direction

    # Mapping of direction words to abbreviations
    direction_map = {
        "North": "N",
        "South": "S",
        "East": "E",
        "West": "W",
        "Northeast": "NE",
        "Northwest": "NW",
        "Southeast": "SE",
        "Southwest": "SW",
    }

    # Split the direction if it's compound (e.g. "North_Northwest")
    parts = direction.split("_")
    abbreviated_parts = [direction_map.get(part, part) for part in parts]

    # Join with space for clarity (e.g. "N NW")
    return " ".join(abbreviated_parts)


def normalize_wind_directions(data):
    """Process wind direction in JSON events list"""
    if isinstance(data, dict):
        return {
            key: convert_wind_direction(value) if key == "wind_speed_direction" else normalize_wind_directions(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [normalize_wind_directions(item) for item in data]
    else:
        return data
