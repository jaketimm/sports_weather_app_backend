# Stand alone script to geocode the track addresses in the data/tracks.json file using the Google Maps API
import os
import sys
import requests
from dotenv import load_dotenv
import logging


# Imports for running from this script's folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.file_utils import load_json, save_json

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("MAPSAPI_KEY")


def geocode_address(address, api_key):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            logger.error("Geocoding error:", data['status'])
    else:
        logger.error("HTTP error:", response.status_code)

    return None, None

# Load JSON
data_path = os.path.join(parent_dir, 'data', 'tracks.json')
track_list = load_json(data_path)

for track in track_list:
    try:
        address = track.get('location')
        if address:
            lat, lng = geocode_address(address, api_key)
            if lat is not None and lng is not None:
                track['latitude'] = lat
                track['longitude'] = lng
                logger.info(f"Geocoded {address}: ({lat}, {lng})")
            else:
                logger.info(f"Failed to geocode {address}")
    except Exception as e:
        logger.error(f"Error processing track {track.get('name', 'unknown')}: {e}")

# Save the updated track list back to JSON file
save_json(track_list, data_path)