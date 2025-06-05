# main.py
import sys
from data_processing.data_processing import get_current_weekend_events
import logging
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, USE_CACHED_DATA_BY_DEFAULT

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():

    # Fetch new data from API (this will save to file)
    get_current_weekend_events(use_cached=USE_CACHED_DATA_BY_DEFAULT)

if __name__ == "__main__":
    main()