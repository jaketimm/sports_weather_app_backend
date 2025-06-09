"""
Module for handling weather API operations and data fetching.
"""
import json
import urllib.parse
import requests
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import (TRACKS_FILE, TRACK_FORECAST_FILE, MAPSAPI_BASE_URL, 
                   API_TIMEOUT, FORECAST_HOURS_BEFORE_EVENT, FORECAST_HOURS_AFTER_EVENT)
from utils.conversion_utils import celsius_to_fahrenheit, kph_to_mph, parse_event_time

logger = logging.getLogger(__name__)

# Cache to store forecasts by location
forecast_cache = {}


def build_weather_url(track_name, api_key, json_file=TRACKS_FILE):
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
            # Build the URL
            params = {
                "key": api_key,
                "location.latitude": latitude,
                "location.longitude": longitude
            }
            return f"{MAPSAPI_BASE_URL}?{urllib.parse.urlencode(params)}"

    logger.error(f"Track '{track_name}' not found in the data.")
    raise ValueError(f"Track '{track_name}' not found in the data.")


def get_forecast(maps_api_url, output_file=TRACK_FORECAST_FILE):
    '''Fetches weather forecast data from the Google Maps API and saves it to a JSON file.'''
    all_forecast_data = {
        "forecastHours": []
    }

    next_url = maps_api_url

    # Loop through paginated results
    while next_url:
        response = requests.get(next_url, timeout=API_TIMEOUT)
        if response.status_code == 200:
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
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Save to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_forecast_data, f, indent=2)

    logger.info(f"Forecast saved to {output_file}")
    return all_forecast_data


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
            logger.warning("Warning: MAPSAPI_KEY environment variable not set. Please check your .env file.")
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


def clear_forecast_cache():
    """Clear the forecast cache."""
    forecast_cache.clear()
    logger.info("Forecast cache cleared")


def get_daily_temperatures(forecast_data, event_date):
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

        # Convert to datetime
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        event_time = datetime.strptime(event_time_str, '%I:%M %p')
        event_datetime = event_date.replace(hour=event_time.hour, minute=event_time.minute)

        # Extract daily high and low temperatures for the event date
        daily_temps = get_daily_temperatures(forecast_data, event_date)

        # Extract forecasts for the event window
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

            # Check if this forecast is within configured hours of event start
            time_diff = forecast_dt - event_datetime
            if timedelta(hours=-FORECAST_HOURS_BEFORE_EVENT) <= time_diff <= timedelta(hours=FORECAST_HOURS_AFTER_EVENT):
                # Get original values and convert units
                temp_fahrenheit = celsius_to_fahrenheit(forecast_hour.get('temperature', {}).get('degrees'))
                feels_like_fahrenheit = celsius_to_fahrenheit(
                    forecast_hour.get('feelsLikeTemperature', {}).get('degrees'))
                wind_speed_mph = kph_to_mph(forecast_hour.get('wind', {}).get('speed', {}).get('value'))

                weather_info = {
                    'time': forecast_dt.strftime('%I:%M %p'),
                    'temperature': temp_fahrenheit,
                    'feels_like': feels_like_fahrenheit,
                    'condition': forecast_hour.get('weatherCondition', {}).get('description', {}).get('text', 'N/A'),
                    'precipitation_type': forecast_hour.get('precipitation', {}).get('probability', {}).get('type',
                                                                                                        'N/A'),
                    'precipitation_prob': forecast_hour.get('precipitation', {}).get('probability', {}).get('percent',
                                                                                                        'N/A'),
                    'wind_speed': wind_speed_mph,
                    'wind_speed_direction': forecast_hour.get('wind', {}).get('direction', {}).get('cardinal', 'N/A')
                }
                relevant_forecasts.append(weather_info)

        # Return both hourly forecasts and daily temperatures
        return {
            'hourly_forecast': relevant_forecasts[:5],  # Limit to 5 hours 
            'daily_high': daily_temps['high'],
            'daily_low': daily_temps['low']
        }

    except Exception as e:
        logger.error(f"Error processing weather for {event.get('location', 'unknown')}: {e}")
        return {}
