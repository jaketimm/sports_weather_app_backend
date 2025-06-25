# Configuration file for NDBC buoy data downloader

# File paths
FILE_PATHS = {
    'data_dir': './NOAA_buoy_api/data/',
    'raw_filename_template': 'buoy_data_current_hour.txt',
    'processed_filename_template': 'processed_buoy_data.csv'
}

# Buoy station IDs to extract
ENABLED_BUOYS = [
    '45029',
    'LDTM4',
    '45168',
    '45198'
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