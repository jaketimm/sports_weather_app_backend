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
DATA_OUTPUT_DIR = os.path.join('/', 'var', 'www', 'html', 'data')
SERIES_SCHEDULES_DIR = os.path.join(DATA_DIR, 'series_schedules')
TRACKS_FILE = os.path.join(DATA_DIR, 'tracks.json')
SCHEDULE_FILE = os.path.join(DATA_DIR, 'schedule.json')
EVENTS_WITH_WEATHER_FILE = os.path.join(DATA_OUTPUT_DIR, 'events_with_weather.json')
TRACK_FORECAST_FILE = os.path.join(DATA_DIR, 'track_forecast.json')
LOG_FILE = os.path.join(BASE_DIR, 'log_file.log')
ALL_LOCATIONS_FORECAST_FILE = os.path.join(DATA_OUTPUT_DIR, 'all_10_day_forecasts.json')

# Individual series schedule files
NASCAR_CUP_SCHEDULE_FILE = os.path.join(SERIES_SCHEDULES_DIR, 'nascar_cup_sched.json')
NASCAR_XFINITY_SCHEDULE_FILE = os.path.join(SERIES_SCHEDULES_DIR, 'nascar_xfinity_sched.json')
NASCAR_TRUCKS_SCHEDULE_FILE = os.path.join(SERIES_SCHEDULES_DIR, 'nascar_trucks_sched.json')
INDYCAR_SCHEDULE_FILE = os.path.join(SERIES_SCHEDULES_DIR, 'indycar_sched.json')
ARCA_SCHEDULE_FILE = os.path.join(SERIES_SCHEDULES_DIR, 'arca_sched.json')
CARS_TOUR_SCHEDULE_FILE = os.path.join(SERIES_SCHEDULES_DIR, 'cars_tour_sched.json')

# List of all schedule files for easy iteration
SERIES_SCHEDULE_FILES = {
    'NASCAR CUP SERIES': NASCAR_CUP_SCHEDULE_FILE,
    'NASCAR XFINITY SERIES': NASCAR_XFINITY_SCHEDULE_FILE,
    'NASCAR TRUCK SERIES': NASCAR_TRUCKS_SCHEDULE_FILE,
    'INDYCAR': INDYCAR_SCHEDULE_FILE,
    'ARCA': ARCA_SCHEDULE_FILE,
    'CARS TOUR': CARS_TOUR_SCHEDULE_FILE,
}

EVENTS_WITH_WEATHER_FILE = os.path.join(DATA_DIR, 'events_with_weather.json')
TRACK_FORECAST_FILE = os.path.join(DATA_DIR, 'track_forecast.json')
ALL_LOCATIONS_FORECAST_FILE = os.path.join(DATA_DIR, 'all_10_day_forecasts.json')
LOG_FILE = os.path.join(BASE_DIR, 'log_file.log')

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Weather Settings
FORECAST_HOURS_BEFORE_EVENT = 1
FORECAST_HOURS_AFTER_EVENT = 4
USE_CACHED_DATA_BY_DEFAULT = False

# Series Options
ENABLED_SERIES = [
    'NASCAR CUP SERIES',
    'NASCAR XFINITY SERIES', 
    'NASCAR TRUCK SERIES',
    'INDYCAR',
    'ARCA',
    'CARS TOUR'
]  # Can be modified to enable/disable specific series

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SERIES_SCHEDULES_DIR, exist_ok=True)