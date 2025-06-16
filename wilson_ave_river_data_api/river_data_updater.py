import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import requests

# configuration settings
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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)



def load_rdb_file_to_df(input_file: str) -> pd.DataFrame:
    """
    Loads an RDB file into a pandas DataFrame.
    
    Args:
        input_file (str): Path to the RDB file.
    
    Returns:
        data: DataFrame containing the RDB data.
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"File not found: {input_file}")
    
        # Read the downloaded RDB file, skipping comment lines
        data = pd.read_csv(input_file,
                            comment='#',
                            sep='\t',
                            skiprows=[0],  # Skip the first non-comment line (format spec)
                            dtype={'agency_cd': str, 'site_no': str})

        # Clean column names (remove any whitespace)
        data.columns = data.columns.str.strip()
        data = data.rename(columns={data.columns[4]: 'level'})
        data = data.astype({'level': float}, errors='ignore')

        # Convert datetime column to proper datetime objects
        data['datetime'] = pd.to_datetime(data['datetime'])

        return data
    
    except Exception as e:
        logger.error(f"Error loading RDB file {input_file}: {e}")
        raise e
    

def create_url(start_dt: datetime, end_dt: datetime, site: str, parameter: str = USGS_DEFAULT_PARAMETER_CODE) -> str:
    """Create formatted URL for data request (adapted from your codebase)."""
    start_str = start_dt.strftime(f"%Y-%m-%dT%H:%M:%S.000{TIMEZONE_OFFSET}")
    end_str = end_dt.strftime(f"%Y-%m-%dT%H:%M:%S.000{TIMEZONE_OFFSET}")
    return (f"{USGS_BASE_URL}?sites={site}&agencyCd={USGS_AGENCY_CODE}&parameterCd={parameter}"
            f"&startDT={start_str}&endDT={end_str}&format=rdb")


def fetch_and_save_recent_data(station_id: str, hours: int = 1) -> bool:
    """
    Fetch the last hour of data from the USGS API, check if it's not empty,
    and save to RIVER_DATA_FILE if valid. Returns True if data was saved successfully.
    Adapted from download_data_single_block in your codebase.
    """
    current_time = datetime.now()
    start_time = current_time - timedelta(hours=hours)
    url = create_url(start_time, current_time, station_id)

    try:
        # Fetch data with timeout (using config value)
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()

        # Process the RDB response line by line (filtering as in your download_data_single_block)
        lines = response.text.split('\n')
        data_to_write = []
        header_written = False
        has_valid_data = False

        for line in lines:
            if not line.strip():
                continue
            if line.startswith('agency_cd') and not header_written:
                data_to_write.append(line)
                header_written = True
            elif line.startswith('USGS'):
                data_to_write.append(line)
                has_valid_data = True  # Mark that we have at least one data row

        if not has_valid_data:
            logger.warning("API response is empty or contains no valid data lines. Skipping save.")
            return False

        # Create directory for RIVER_DATA_FILE if it doesn't exist
        os.makedirs(os.path.dirname(RIVER_DATA_FILE), exist_ok=True)

        # Write processed data to RIVER_DATA_FILE
        with open(RIVER_DATA_FILE, 'w') as f:
            f.write("# USGS River Level Data\n")
            if data_to_write:
                f.write('\n'.join(data_to_write) + '\n')

        logger.info(f"Successfully fetched and saved data to {RIVER_DATA_FILE} from {url}")
        return True

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return False
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        return False
    except Exception as e:
        logger.error(f"Error fetching or saving data: {str(e)}")
        return False


def append_to_csv(csv_file: str):
    """Load existing CSV and RDB file, combine them, and save back to CSV."""
    # Load the new data from RIVER_DATA_FILE
    try:
        new_df = load_rdb_file_to_df(RIVER_DATA_FILE)
        if new_df.empty:
            logger.warning(f"{RIVER_DATA_FILE} loaded but is empty. Skipping append.")
            return
        logger.info(f"Loaded {len(new_df)} rows from {RIVER_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error loading {RIVER_DATA_FILE}: {str(e)}. Skipping append.")
        return

    # Load the existing CSV or initialize if it doesn't exist
    if not os.path.exists(csv_file):
        logger.info(f"CSV file does not exist: {csv_file}. Creating new file from RDB data.")
        new_df.to_csv(csv_file, index=False)
        return

    try:
        existing_df = pd.read_csv(csv_file)
        logger.info(f"Loaded {len(existing_df)} rows from existing {csv_file}")
    except Exception as e:
        logger.error(f"Error reading existing CSV: {str(e)}. Treating as new file.")
        new_df.to_csv(csv_file, index=False)
        return

    # Combine DataFrames (append without unifying columns, as per your request)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Remove duplicates (based on site_no and datetime, keeping latest) and sort for consistency
    if 'site_no' in combined_df.columns and 'datetime' in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=['site_no', 'datetime'], keep='last')
        combined_df = combined_df.sort_values(['site_no', 'datetime'])

    # Save the combined DataFrame back to CSV
    combined_df.to_csv(csv_file, index=False)
    logger.info(f"Appended {len(new_df)} new rows to {csv_file}. Total rows after update: {len(combined_df)}")


def update_wilson_ave_river_data():
    # Constants for this script
    STATION_ID = "04119070"
    CSV_FILE = DATA_OUTPUT_FILE
    HOURS = 6

    logger.info(f"Starting data append for station {STATION_ID} (last {HOURS} hour(s)) to {CSV_FILE}")

    # Fetch and save recent data to RIVER_DATA_FILE
    data_saved = fetch_and_save_recent_data(STATION_ID, HOURS)

    # If data was saved successfully, proceed to append
    if data_saved:
        append_to_csv(CSV_FILE)
    else:
        logger.warning("No valid data was saved to RIVER_DATA_FILE. Skipping append.")

    logger.info("Script completed.")



    