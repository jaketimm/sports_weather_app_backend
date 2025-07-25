"""
Module for handling event data processing and management.
"""
import logging
from datetime import datetime, timedelta
from racing_weather_api.config import (
    EVENTS_WITH_WEATHER_FILE, SCHEDULE_FILE, TRACKS_FILE,
    SERIES_SCHEDULE_FILES, ENABLED_SERIES
)
from racing_weather_api.utils.file_utils import load_json, save_json
from racing_weather_api.utils.conversion_utils import parse_datetime, normalize_text_case, normalize_wind_directions, convert_start_time_utc, parse_event_time
from racing_weather_api.api.weather_api import get_weather_for_event, clear_forecast_cache

logger = logging.getLogger(__name__)

# Constants for data files
DEFAULT_SCHEDULE_FILE = SCHEDULE_FILE


def load_schedules_from_series(series_list=None):
    """Load and combine schedule data from multiple series files.
    
    Args:
        series_list: List of series names to load. If None, uses ENABLED_SERIES from config.
    
    Returns:
        Combined list of all events from specified series.
    """
    if series_list is None:
        series_list = ENABLED_SERIES
        
    combined_schedule = []
    
    for series_name in series_list:
        if series_name in SERIES_SCHEDULE_FILES:
            schedule_file = SERIES_SCHEDULE_FILES[series_name]
            try:
                series_data = load_json(schedule_file)
                if series_data:
                    combined_schedule.extend(series_data)
            except Exception as e:
                logger.error(f"Error loading schedule for {series_name}: {e}")
        else:
            logger.warning(f"No schedule file configured for series: {series_name}")
    
    logger.info(f"Total events loaded: {len(combined_schedule)}")
    return combined_schedule


def get_events_with_weather(schedule_file=None, use_cached=True, series_list=None):
    """Get events for the current weekend (Friday to Sunday) with weather data.

    Args:
        schedule_file: Path to a single schedule JSON file (for backward compatibility)
        use_cached: Whether to use cached event data with weather if available
        series_list: List of series names to include. If None, uses ENABLED_SERIES.
    """
    try:
        if not use_cached:
            clear_forecast_cache()  # Clear old cached forecasts on refresh

        # Calculate the Monday of the current week for caching key
        today = datetime.now()
        weekday = today.weekday()  # 0 = Monday, 6 = Sunday
        monday = today - timedelta(days=weekday)  # Start of the week
        monday_str = monday.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD

        # Check if we have cached data and should use it
        if use_cached:
            cached_events = load_events_with_weather()
            if cached_events and monday_str in cached_events:
                logger.info(f"Using cached events with weather data for week of {monday_str}")
                return cached_events[monday_str]

        # Load schedule data - either from single file or multiple series files
        if schedule_file:
            # Use single file if specified (backward compatibility)
            logger.info(f"Loading schedule from single file: {schedule_file}")
            schedule_data = load_json(schedule_file)
        else:
            # Load from multiple series files
            logger.info(f"Loading schedules from series files")
            schedule_data = load_schedules_from_series(series_list)
            
        track_info_file = load_json(TRACKS_FILE)

        # Filter events for the current week (Monday to Sunday)
        current_week_events = get_next_7_days_events(schedule_data)

        # Remove events that have already happened
        filtered_events = exclude_past_events(current_week_events)

        # Loop through each event add matched track details and create new datetime key
        for event in filtered_events:
            
            # create datetime 
            combined_dt = parse_datetime(event.get('date', ''), event.get('time', ''))
            event_time_est = combined_dt.strftime("%Y-%m-%d %H:%M") # Combined date+time as a string
            event['start_time_UTC'] = convert_start_time_utc(event_time_est)

            # find event track
            matching_track = next(
                (track for track in track_info_file if track['name'] == event['location']),
                None
            )
            if matching_track:
                # Add specific location details and speedway name
                event['track_location'] = matching_track['location']
                event['track_name'] = matching_track['trackName']
                event['track_latitude'] = matching_track['latitude']
                event['track_longitude'] = matching_track['longitude']
            else:
                logger.warning(f"No match found for event location: {event['location']}")

        # Get weather data for filtered events
        for event in filtered_events:
            weather_data = get_weather_for_event(event)
            event['weather'] = weather_data
            logger.info(f"Processed weather data for event at {event['location']}")

        # Sort events by date and time for consistent display
        filtered_events.sort(key=lambda e: e['start_time_UTC'])

        # Clean up text case, convert wind dir. to N,E,S,W
        filtered_events = normalize_text_case(filtered_events)
        filtered_events = normalize_wind_directions(filtered_events)

        # Save the events with weather to JSON file 
        weekend_events = {monday_str: filtered_events}
        save_events_with_weather(weekend_events)

        return filtered_events

    except Exception as e:
        logger.error(f"Error processing weather data: {e}")
        return []


def get_next_7_days_events(schedule_data):
    """Filter events to only include those in the next 7 days from today."""
    try:
        if not schedule_data:
            return []

        # Calculate the next 7 days date range
        today = datetime.now()
        start_date = today
        end_date = today + timedelta(days=7)  # Next 7 days + today 
        
        # Convert to date strings for comparison
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        next_7_days_events = []
        
        for event in schedule_data:
            event_date = event.get('date', '')
            if event_date and start_date_str <= event_date <= end_date_str:
                next_7_days_events.append(event)

        logger.info(f"Found {len(next_7_days_events)} events for next 7 days {start_date_str} to {end_date_str}")
        return next_7_days_events

    except Exception as e:
        logger.error(f"Error filtering next 7 days events: {e}")
        return []


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

                    # Dont't exclude events until 2 hrs after start time
                    if current_time <= event_datetime + timedelta(hours=2):
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
        logger.error(f"Error filtering past events: {e}")
        return []
    
def save_events_with_weather(events_with_weather, file_path=EVENTS_WITH_WEATHER_FILE):
    """Save events with weather data to a JSON file."""
    return save_json(events_with_weather, file_path)


def load_events_with_weather(file_path=EVENTS_WITH_WEATHER_FILE):
    """Load events with weather data from a JSON file."""
    return load_json(file_path)
