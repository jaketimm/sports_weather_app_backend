"""
Module for handling event data processing and management.
"""
import logging
from datetime import datetime, timedelta
from racing_weather_api.config import EVENTS_WITH_WEATHER_FILE, SCHEDULE_FILE, TRACKS_FILE
from racing_weather_api.utils.file_utils import load_json, save_json
from racing_weather_api.utils.conversion_utils import parse_event_time, normalize_text_case, normalize_wind_directions
from racing_weather_api.api.weather_api import get_weather_for_event, clear_forecast_cache

logger = logging.getLogger(__name__)

# Constants for data files
DEFAULT_SCHEDULE_FILE = SCHEDULE_FILE


def get_events_with_weather(schedule_file=DEFAULT_SCHEDULE_FILE, use_cached=True):
    """Get events for the current weekend (Friday to Sunday) with weather data.

    Args:
        schedule_file: Path to the schedule JSON file
        use_cached: Whether to use cached event data with weather if available
    """
    try:

        if not use_cached:
            clear_forecast_cache()  # Clear old cached forecasts on refresh

        # Calculate the Friday of the current week
        today = datetime.now()
        weekday = today.weekday()  # 0 = Monday, 6 = Sunday
        monday = today - timedelta(days=weekday)  # Start of the week
        friday = monday + timedelta(days=4)
        friday_str = friday.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD

        # Check if we have cached data and should use it
        if use_cached:
            cached_events = load_events_with_weather()
            if cached_events and friday_str in cached_events:
                logger.info(f"Using cached events with weather data for {friday_str}")
                return cached_events[friday_str]

        # Load JSON schedule data
        schedule_data = load_json(schedule_file)
        track_info_file = load_json(TRACKS_FILE)

        # Get any events for the current weekend (Fri - Sun)
        events = schedule_data.get(friday_str, []) if schedule_data else []

        # Remove events that have already happened
        filtered_events = exclude_past_events(events)

        # Loop through each event and add matched track location e.g. MICHIGAN => Brooklyn, MI
        for event in events:
            matching_track = next(
                (track for track in track_info_file if track['name'] == event['location']),
                None
            )
            if matching_track:
                # Add specific location
                event['track_location'] = matching_track['location']
            else:
                logger.warning(f"No match found for event location: {event['location']}")

        # Get weather data for filtered events
        for event in filtered_events:
            weather_data = get_weather_for_event(event)
            event['weather'] = weather_data

        logger.info("Forecast data successfully download and processed")

        # Sort events by date for consistent display
        filtered_events.sort(key=lambda e: e.get('date', ''))

        # Clean up text case, convert wind dir. to N,E,S,W
        filtered_events = normalize_text_case(filtered_events)
        filtered_events = normalize_wind_directions(filtered_events)

        # Save the events with weather to JSON file
        weekend_events = {friday_str: filtered_events}
        save_events_with_weather(weekend_events)

        return filtered_events

    except Exception as e:
        logger.error(f"Error processing weather data{e}")
        return {}


def exclude_past_events(events):
    """Filter events to only include future or current events."""
    try:
        current_time = datetime.now()
        filtered_events = []

        for event in events:
            event_date_str = event.get('date', '')
            event_time_str = event.get('time', '')

            if event_date_str and event_time_str:
                try:
                    # Standardize the time format
                    std_time_str = parse_event_time(event_time_str)

                    # Parse the datetime
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                    event_time = datetime.strptime(std_time_str, '%I:%M %p')
                    event_datetime = event_date.replace(hour=event_time.hour, minute=event_time.minute)

                    if event_datetime >= current_time:
                        filtered_events.append(event)
                except ValueError as e:
                    logger.error(f"Error parsing event time: {e}")
                    # If parsing fails, include the event anyway
                    filtered_events.append(event)
            else:
                # Include events without date/time
                filtered_events.append(event)

        return filtered_events

    except Exception as e:
        logger.error(f"Error processing weather data{e}")
        return {}


def save_events_with_weather(events_with_weather, file_path=EVENTS_WITH_WEATHER_FILE):
    """Save events with weather data to a JSON file."""
    return save_json(events_with_weather, file_path)


def load_events_with_weather(file_path=EVENTS_WITH_WEATHER_FILE):
    """Load events with weather data from a JSON file."""
    return load_json(file_path)
