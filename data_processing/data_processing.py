import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from maps_API.maps_API_data_processing import build_weather_url, get_forecast

logger = logging.getLogger(__name__)

# Cache to store forecasts by location
forecast_cache = {}

# Constants for data files
EVENTS_DATA_FILE = 'data/events_with_weather.json'
DEFAULT_SCHEDULE_FILE = 'data/schedule.json'


def get_current_weekend_events(schedule_file=DEFAULT_SCHEDULE_FILE, use_cached=True):
    """Get events for the current weekend (Friday to Sunday) with weather data.

    Args:
        schedule_file: Path to the schedule JSON file
        use_cached: Whether to use cached event data with weather if available
    """
    if not use_cached:
        forecast_cache.clear()  # Clear old cached forecasts on refresh

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

    # Get any events for the current weekend
    events = schedule_data.get(friday_str, []) if schedule_data else []

    # Filter events that are in the future or current
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
                    # We'll add the weather data after collecting all events
                    filtered_events.append(event)
            except ValueError as e:
                logger.error(f"Error parsing event time: {e}")
                # If parsing fails, include the event
                filtered_events.append(event)
        else:
            filtered_events.append(event)

    # Get weather data for all events after filtering
    for event in filtered_events:
        weather_data = get_weather_for_event(event)
        event['weather'] = weather_data

    # Sort events by date for consistent display
    filtered_events.sort(key=lambda e: e.get('date', ''))

    # log cache statistics
    logger.info(f"Forecast cache has data for {len(forecast_cache)} locations")
    
    # Save the events with weather to a JSON file for future use
    # Store as a dictionary with the weekend date as the key
    weekend_events = {friday_str: filtered_events}
    save_events_with_weather(weekend_events)

    return True


def get_weather_for_event(event: str):
    """Get 4 hours of weather forecast for an event starting from event time."""
    try:
        location = event.get('location', '')
        event_date_str = event.get('date', '')
        event_time_str = event.get('time', '')
        
        if not all([location, event_date_str, event_time_str]):
            return []
        
        # Get forecast data for this location
        forecast_data = get_location_forecast(location)
        if not forecast_data:
            return []

        # Parse event time
        event_time_str = parse_event_time(event_time_str)
        
        # Convert to datetime
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        event_time = datetime.strptime(event_time_str, '%I:%M %p')
        event_datetime = event_date.replace(hour=event_time.hour, minute=event_time.minute)

        # Extract 4 hours of forecast starting from event time
        forecast_hours = forecast_data.get('forecastHours', [])
        relevant_forecasts = []
        
        for forecast_hour in forecast_hours:
            # Parse the forecast time
            display_time = forecast_hour.get('displayDateTime', {})
            forecast_dt = datetime(
                year=display_time.get('year', 0),
                month=display_time.get('month', 0),
                day=display_time.get('day', 0),
                hour=display_time.get('hours', 0),
                minute=display_time.get('minutes', 0)
            )
            
            # Check if this forecast is within 4 hours of event start
            time_diff = forecast_dt - event_datetime
            if timedelta(hours=-1) <= time_diff <= timedelta(hours=4):
                weather_info = {
                    'time': forecast_dt.strftime('%I:%M %p'),
                    'temperature': forecast_hour.get('temperature', {}).get('degrees', 'N/A'),
                    'temperature_unit': forecast_hour.get('temperature', {}).get('unit', 'CELSIUS'),
                    'feels_like': forecast_hour.get('feelsLikeTemperature', {}).get('degrees', 'N/A'),
                    'feels_like_unit': forecast_hour.get('feelsLikeTemperature', {}).get('unit', 'CELSIUS'),
                    'condition': forecast_hour.get('weatherCondition', {}).get('description', {}).get('text', 'N/A'),
                    'precipitation_type': forecast_hour.get('precipitation', {}).get('probability', {}).get('type', 'N/A'),
                    'precipitation_prob': forecast_hour.get('precipitation', {}).get('probability', {}).get('percent', 'N/A'),
                    'wind_speed': forecast_hour.get('wind', {}).get('speed', {}).get('value', 'N/A'),
                    'wind_speed_unit': forecast_hour.get('wind', {}).get('speed', {}).get('unit', 'Kph'),
                    'wind_speed_direction': forecast_hour.get('wind', {}).get('direction', {}).get('cardinal', 'N/A')
                }
                relevant_forecasts.append(weather_info)
        
        return relevant_forecasts[:4]  # Limit to 4 hours
        
    except Exception as e:
        logger.error(f"Error processing weather for {event.get('location', 'unknown')}: {e}")
        return []
    
    
def get_location_forecast(location: str):
    """Get forecast data for a location, using cache if available."""
    # Check if we already have forecast data for this location
    if location in forecast_cache:
        logger.info(f"Using cached forecast for {location}")
        return forecast_cache[location]
    
    try:
        # Load variables from .env into environment
        load_dotenv()
        # Access the API key
        api_key = os.getenv("MAPSAPI_KEY")
        if not api_key:
            logger.warning("Warning: MAPSAPI_KEY environment variable not set")
            return None
        
        # Build weather URL
        weather_url = build_weather_url(location, api_key)

        logger.info("Downloading data from Google Weather API...")
        # Get forecast data
        forecast_data = get_forecast(weather_url)

        # Cache the result
        forecast_cache[location] = forecast_data
        logger.info(f"Downloaded and cached forecast for {location}")
        
        return forecast_data
    except Exception as e:
        logger.error(f"Error getting forecast for {location}: {e}")
        return None
    

def load_json(file_path: str): 
    """Load JSON from file, return dict or None on error."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading JSON: {e}")  # Log to console for debugging
        return None



def parse_event_time(event_time_str: str):
    """Parse event time string into a standardized format."""
    event_time_str = event_time_str.strip().lower()
    if ':' not in event_time_str:
        event_time_str = event_time_str.replace(' am', ':00 AM').replace(' pm', ':00 PM')
    else:
        event_time_str = event_time_str.upper()
    
    return event_time_str


def save_events_with_weather(events_with_weather: json, file_path=EVENTS_DATA_FILE):
    """Save events with weather data to a JSON file."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(events_with_weather, f, indent=2)
        logger.info(f"Saved events with weather data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving events with weather data: {e}")
        return False


def load_events_with_weather(file_path=EVENTS_DATA_FILE):
    """Load events with weather data from a JSON file."""
    return load_json(file_path)



