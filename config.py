"""
Simple configuration file for the racing weather application
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# API Settings
MAPSAPI_BASE_URL = "https://weather.googleapis.com/v1/forecast/hours:lookup"
API_TIMEOUT = 30  # seconds

# File Paths
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATA_OUPUT_DIR = os.path.join('/', 'var', 'www', 'html', 'data')
TRACKS_FILE = os.path.join(DATA_DIR, 'tracks.json')
SCHEDULE_FILE = os.path.join(DATA_DIR, 'schedule.json')
EVENTS_WITH_WEATHER_FILE = os.path.join(DATA_OUPUT_DIR, 'events_with_weather.json')
TRACK_FORECAST_FILE = os.path.join(DATA_DIR, 'track_forecast.json')
LOG_FILE = os.path.join(BASE_DIR, 'log_file.log')

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Weather Settings
FORECAST_HOURS_BEFORE_EVENT = 1
FORECAST_HOURS_AFTER_EVENT = 4
USE_CACHED_DATA_BY_DEFAULT = False

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
