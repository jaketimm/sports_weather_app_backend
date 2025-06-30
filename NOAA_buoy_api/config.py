# Configuration file for NDBC buoy data downloader
import os


# File paths
FILE_PATHS = {
    'data_dir': './NOAA_buoy_api/data/',
    'output_data_dir': os.path.join('/', 'var', 'www', 'html', 'data'),
    'raw_filename_template': 'buoy_data_current_hour.txt',
    'processed_filename_template': 'processed_buoy_data.csv'
}

# Buoy station IDs to extract
ENABLED_BUOYS = [
    '45029',    # Holland, MI
    'LDTM4',    # Ludington, MI
    '45168',    # South Haven, MI
    '45198',    # Chicago, IL
    '45026',    # Stevensville, MI
    '45022',    # Petosky, MI
    '45194',    # Mackinac, MI
    '45170',    # Michigan City, IN
    '45186',    # Waukegan, WI
    '45014',    # Green Bay, WI
]

# Data fields to extract (in order they will appear in output)
# Available fields: WDIR, WSPD, GST, WVHT, DPD, APD, MWD, PRES, ATMP, WTMP, DEWP, VIS, PTDY, TIDE
ENABLED_FIELDS = [
    'WDIR',    # Wind Direction (
    'WSPD',    # Wind Speed 
    'ATMP',    # Air Temperature 
    'WVHT',    # Wave Height 
    'WTMP'     # Water Temperature 
]

# Unit conversion settings
CONVERSIONS = {
    'convert_wspd_to_mph': True,           # Convert m/s to mph
    'convert_wvht_to_feet': True,          # Convert meters to feet
    'convert_atmp_to_fahrenheit': True,    # Convert Celsius to Fahrenheit
    'convert_wtmp_to_fahrenheit': True     # Convert Celsius to Fahrenheit
}

# Other settings
SETTINGS = {
    'request_timeout': 30,
    'missing_value_placeholder': 'N/A',
    'only_top_of_hour': True  # Only extract data from the top of the hour (mm == '00')
}