# main.py
import sys
from data_processing.data_processing import get_current_weekend_events
import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'log_file.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():

    # Fetch new data from API (this will save to file)
    events = get_current_weekend_events(use_cached=True)

if __name__ == "__main__":
    main()