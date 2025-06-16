# config.py
# Central configuration file for Water Level & Temperature Tracking System
# Contains essential parameters and configuration variables

import os

###########################################
# Paths and File Settings
###########################################
# Base directory is the directory where this config file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data files with updated paths
STATION_LIST_FILE = os.path.join(BASE_DIR, 'data', 'station_list_mi.csv')
RIVER_DATA_FILE = os.path.join(BASE_DIR, 'data', 'river_level_data.rdb')
LOG_FILE = os.path.join(BASE_DIR, 'log_file.log')
DATA_OUTPUT_DIR = os.path.join('/', 'var', 'www', 'html', 'data')
DATA_OUTPUT_FILE = os.path.join(DATA_OUTPUT_DIR, 'river_data_m-11.csv')

###########################################
# USGS API Settings
###########################################
# Base URL for API requests
USGS_BASE_URL = "https://waterservices.usgs.gov/nwis/iv/"
# Default parameter code (00065 = Gage height, ft)
USGS_DEFAULT_PARAMETER_CODE = "00065"
# Agency code
USGS_AGENCY_CODE = "USGS"
# Time zone offset for API requests
TIMEZONE_OFFSET = "-04:00"
# Request timeout in seconds
API_TIMEOUT = 10


