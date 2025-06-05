import json
import urllib.parse
import requests
import os
import logging
from config import TRACKS_FILE, TRACK_FORECAST_FILE, MAPSAPI_BASE_URL, API_TIMEOUT

logger = logging.getLogger(__name__)

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

    
