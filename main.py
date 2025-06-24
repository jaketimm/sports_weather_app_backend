import logging
from racing_weather_api.config import LOG_FILE, LOG_LEVEL, LOG_FORMAT
from racing_weather_api.data_processing.event_processing import get_events_with_weather

import os
import json

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Enable for production deployment
    ]
)
logger = logging.getLogger(__name__)


try:

    events = get_events_with_weather(use_cached=False)

    if events:
        logger.info(f"Retrieved {len(events)} events for the current weekend")
    else:
        logger.warning("No events found for the current weekend")
    
    #create an empty file for testing no events logic on website

    # Define the path and filename
    file_path = os.path.join('/', 'var', 'www', 'html', 'data', 'empty.json')

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Define the JSON data
    data = {
        "2025-06-13": []
    }

    # Write the JSON data to the file
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=2)

    print(f"File created at: {file_path}")


except Exception as e:
    logger.error(f"Error in scheduled job: {str(e)}")

