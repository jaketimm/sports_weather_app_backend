"""
Utility functions for handling units conversion and data formatting.
"""
import logging

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


def parse_event_time(event_time_str: str):
    """Parse event time string into a standardized format."""
    event_time_str = event_time_str.strip().lower()
    if ':' not in event_time_str:
        event_time_str = event_time_str.replace(' am', ':00 AM').replace(' pm', ':00 PM')
    else:
        event_time_str = event_time_str.upper()

    return event_time_str
