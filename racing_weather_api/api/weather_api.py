"""
Module for handling weather API operations and data fetching.
"""
import json
import urllib.parse
import requests
import os
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from racing_weather_api.config import (TRACKS_FILE, TRACK_FORECAST_FILE, MAPSAPI_BASE_URL, ALL_LOCATIONS_FORECAST_FILE,
                                       API_TIMEOUT, FORECAST_HOURS_BEFORE_EVENT, FORECAST_HOURS_AFTER_EVENT)
from racing_weather_api.utils.conversion_utils import celsius_to_fahrenheit, kph_to_mph, parse_event_time, convert_est_to_utc, convert_utc_to_est

logger = logging.getLogger(__name__)

# Cache to store forecasts by location
forecast_cache = {}

def get_weather_for_event(event: dict):
    """Get weather forecast for an event including hourly forecasts and daily high/low temperatures."""
    try:
        location = event.get('location', '')
        event_date_str = event.get('date', '')
        event_time_str = event.get('time', '')

        if not all([location, event_date_str, event_time_str]):
            return {}

        # Get forecast data for this location
        forecast_data = get_location_forecast(location)
        if not forecast_data:
            return {}

        # Parse event time
        event_time_str = parse_event_time(event_time_str)

        # Convert EST event time from schedule file to UTC
        event_datetime_utc = convert_est_to_utc(event_date_str, event_time_str)
        if not event_datetime_utc:
            return {}

        # Get current time in UTC for dynamic window calculation
        current_time_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        # Extract daily high and low temperatures for the event date (use original date)
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        daily_max_min = extract_daily_high_low_temps(forecast_data, event_date)

        # Extract hours from weather file
        forecast_hours = forecast_data.get('forecastHours', [])
        relevant_forecasts = []

        # Calculate dynamic forecast window based on current time and event time
        if current_time_utc < event_datetime_utc:
            # Event hasn't started yet - show 2 hours before event to 3 hours after
            window_start = event_datetime_utc - timedelta(hours=FORECAST_HOURS_BEFORE_EVENT)
            window_end = event_datetime_utc + timedelta(hours=FORECAST_HOURS_AFTER_EVENT)
        else:
            # Event has started - show from current time to original end time (shrinking window)
            window_start = current_time_utc
            window_end = event_datetime_utc + timedelta(hours=(FORECAST_HOURS_AFTER_EVENT-1))

        # Save forecast data within the calculated window
        for forecast_hour in forecast_hours:
            # Parse the forecast time (assuming this is in UTC from Google API)
            start_time = forecast_hour.get('startTime', '')
            if start_time:
                # Parse UTC timestamp: "2025-06-27T18:00:00Z"
                forecast_dt_utc = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                forecast_dt_utc = forecast_dt_utc.replace(tzinfo=None)  # Remove timezone info for comparison
            else:
                # Fallback to displayDateTime if startTime not available
                display_time = forecast_hour.get('displayDateTime', {})
                forecast_dt_utc = datetime(
                    year=display_time.get('year', 0),
                    month=display_time.get('month', 0),
                    day=display_time.get('day', 0),
                    hour=display_time.get('hours', 0),
                    minute=display_time.get('minutes', 0)
                )

            # Check if this forecast is within the calculated window
            if window_start <= forecast_dt_utc <= window_end:
                # Get original values and convert units
                temp_fahrenheit = celsius_to_fahrenheit(forecast_hour.get('temperature', {}).get('degrees'))
                feels_like_fahrenheit = celsius_to_fahrenheit(
                    forecast_hour.get('feelsLikeTemperature', {}).get('degrees'))
                wind_speed_mph = kph_to_mph(forecast_hour.get('wind', {}).get('speed', {}).get('value'))

                # Convert UTC time back to EST for display
                forecast_dt_est = convert_utc_to_est(forecast_dt_utc)

                # Save hourly weather conditions
                weather_info = {
                    'time': forecast_dt_est.strftime('%I:%M %p'),
                    'temperature': temp_fahrenheit,
                    'feels_like': feels_like_fahrenheit,
                    'condition': forecast_hour.get('weatherCondition', {}).get('description', {}).get('text', 'N/A'),
                    'precipitation_type': forecast_hour.get('precipitation', {}).get('probability', {}).get('type', 'N/A'),
                    'precipitation_prob': forecast_hour.get('precipitation', {}).get('probability', {}).get('percent', 'N/A'),
                    'wind_speed': wind_speed_mph,
                    'wind_speed_direction': forecast_hour.get('wind', {}).get('direction', {}).get('cardinal', 'N/A')
                }
                relevant_forecasts.append(weather_info)

        # Return both hourly forecasts and daily high/low temperatures
        return {
            'hourly_forecast': relevant_forecasts[:5],  # Limit to 5 hours
            'daily_high': daily_max_min['high'],
            'daily_low': daily_max_min['low']
        }

    except Exception as e:
        logger.error(f"Error processing weather for {event.get('location', 'unknown')}: {e}")
        return {}


def get_location_forecast(location: str):
    """Get forecast data for a location, using cache if available."""

    # Check if we already have forecast data for this location (avoid redundant 10-day weather downloads)
    if location in forecast_cache:
        logger.info(f"Using cached forecast for {location}, data already downloaded")
        return forecast_cache[location]

    try:
        # Load variables from .env into environment
        load_dotenv()
        # Access the API key
        api_key = os.getenv("MAPSAPI_KEY")
        if not api_key:
            logger.warning("Warning: MAPSAPI_KEY environment variable not set. Please check your .env file.")
            return None

        # Build weather URL
        weather_url = build_weather_api_url(location, api_key)

        logger.info("Downloading data from Google Weather API...")
        # Get forecast data
        forecast_data = download_maps_api_data(weather_url)

        # Cache the result
        forecast_cache[location] = forecast_data

        # Process and save the forecast data to all locations forecasts file
        save_10_day_location_forecast(forecast_data, location)

        logger.info(f"Downloaded and cached forecast for {location}")

        return forecast_data
    except Exception as e:
        logger.error(f"Error getting forecast for {location}: {e}")
        return None


def build_weather_api_url(track_name, api_key, json_file=TRACKS_FILE):
    '''Builds a weather forecast URL for a given track name using the Google Maps API.'''
    # Load the track data from JSON
    with open(json_file, 'r') as file:
        tracks = json.load(file)

    # Normalize input to allow case-insensitive match
    track_name = track_name.strip().upper()

    # Find the matching track
    for track in tracks:
        if track['name'].upper() == track_name:
            latitude = track['latitude']
            longitude = track['longitude']
            # Build the URL, MAPS API uses latitude and longitude for location
            params = {
                "key": api_key,
                "location.latitude": latitude,
                "location.longitude": longitude
            }
            return f"{MAPSAPI_BASE_URL}?{urllib.parse.urlencode(params)}"

    logger.error(f"Track '{track_name}' not found in the data.")
    raise ValueError(f"Track '{track_name}' not found in the data.")


def download_maps_api_data(maps_api_url, output_file=TRACK_FORECAST_FILE):
    '''Fetches weather forecast data from the Google Maps API and saves it to a JSON file.'''
    all_forecast_data = {
        "forecastHours": []
    }

    next_url = maps_api_url

    # Loop through paginated results
    while next_url:
        try:
            response = make_api_request(next_url)
            data = response.json()

            # Append current page's forecast data
            hours = data.get("forecastHours", [])
            all_forecast_data["forecastHours"].extend(hours)

            # Check for next page
            next_page_token = data.get("nextPageToken")
            if next_page_token:
                # Add pageToken to the base URL
                next_url = f"{maps_api_url}&pageToken={urllib.parse.quote(next_page_token)}"
            else:
                next_url = None  # Done
                
        except Exception as e:
            logger.error(f"Failed to download API data: {e}")
            raise

    # Save to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_forecast_data, f, indent=2)

    logger.info(f"Forecast saved to {output_file}")
    return all_forecast_data


# API retry logic using tenacity
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((
        requests.exceptions.RequestException,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)

def make_api_request(url):
    """Make API request with retry logic using tenacity."""
    response = requests.get(url, timeout=API_TIMEOUT)
    
    # Retry on server errors and rate limiting
    if response.status_code in [429, 500, 502, 503, 504]:
        raise requests.exceptions.RequestException(f"API request failed with status code {response.status_code}")
    elif response.status_code != 200:
        # Don't retry on client errors (4xx except 429)
        logger.error(f"API request failed with non-retryable status code {response.status_code}")
        raise Exception(f"API request failed with status code {response.status_code}")
    
    return response



def clear_forecast_cache():
    """Clear the forecast cache and saved all-locations 10 days forecasts file."""
    forecast_cache.clear()

    # Clear the forecast file 
    with open(ALL_LOCATIONS_FORECAST_FILE, 'w') as f:
        json.dump({}, f)

    logger.info("Forecast cache cleared")


def extract_daily_high_low_temps(forecast_data, event_date):
    """Extract daily high and low temperatures for the given date from forecast data."""
    try:
        # Get hourly forecast data
        forecast_hours = forecast_data.get('forecastHours', [])

        # Collect all temperatures for the event date
        daily_temperatures = []

        for forecast_hour in forecast_hours:
            display_time = forecast_hour.get('displayDateTime', {})
            forecast_dt = datetime(
                year=display_time.get('year', 0),
                month=display_time.get('month', 0),
                day=display_time.get('day', 0),
                hour=display_time.get('hours', 0),
                minute=display_time.get('minutes', 0)
            )

            # Check if this forecast is for the same date as the event
            if forecast_dt.date() == event_date.date():
                temp_data = forecast_hour.get('temperature', {})
                temp_value = temp_data.get('degrees')
                if temp_value is not None:
                    # Convert Celsius to Fahrenheit
                    temp_fahrenheit = celsius_to_fahrenheit(temp_value)
                    daily_temperatures.append(temp_fahrenheit)

        if daily_temperatures:
            return {
                'high': max(daily_temperatures),
                'low': min(daily_temperatures)
            }
        else:
            # No temperature data found for the date
            return {
                'high': 'N/A',
                'low': 'N/A'
            }

    except Exception as e:
        logger.error(f"Error extracting daily temperatures: {e}")
        return {
            'high': 'N/A',
            'low': 'N/A'
        }


def format_display_time(display_datetime):
    """Format the display time to a readable string"""
    year = display_datetime['year']
    month = str(display_datetime['month']).zfill(2)
    day = str(display_datetime['day']).zfill(2)
    hours = str(display_datetime['hours']).zfill(2)
    minutes = str(display_datetime['minutes']).zfill(2)
    
    return f"{year}-{month}-{day} {hours}:{minutes}"


def save_10_day_location_forecast(forecast_data, location, json_file=TRACKS_FILE):
    """Save 10 day track temp/precipication forecast to ALL_LOCATIONS_FORECAST_FILE.json"""
    try:
        # Load existing data if file exists  
        try:
            with open(ALL_LOCATIONS_FORECAST_FILE, 'r') as f:
                all_locations_data = json.load(f)
        except FileNotFoundError:
            all_locations_data = {}
        
        # Load tracks and extract the track/speedway name
        with open(json_file, 'r') as file:
            tracks = json.load(file)

        for track in tracks:
            if track['name'].upper() == location:
                track_name = track['trackName']

        # Process the forecast data for this location
        processed_hours = []
        
        if 'forecastHours' in forecast_data:
            for hour in forecast_data['forecastHours']:
                processed_hour = {
                    "time": format_display_time(hour['displayDateTime']),
                    "tempFahrenheit": round(celsius_to_fahrenheit(hour['temperature']['degrees']), 1),
                    "precipitationPercent": hour['precipitation']['probability']['percent']
                }
                processed_hours.append(processed_hour)
        
        # Add this location's data to the all location foreacast file
        all_locations_data[track_name] = {
            "forecastHours": processed_hours
        }
        
        # Save back to file
        with open(ALL_LOCATIONS_FORECAST_FILE, 'w') as f:
            json.dump(all_locations_data, f, indent=2)
        
        logger.info(f"Processed and saved forecast data for {location} to {ALL_LOCATIONS_FORECAST_FILE}")
        
    except Exception as e:
        logger.error(f"Error processing and saving forecast data for {location}: {e}")