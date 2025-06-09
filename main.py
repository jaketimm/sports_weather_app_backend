# main.py
import sys
import logging
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, USE_CACHED_DATA_BY_DEFAULT
from data_processing.event_processing import get_current_weekend_events

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
    """Main entry point for the racing weather application."""
    # Fetch new data from API (this will save to file)
    events = get_current_weekend_events(use_cached=USE_CACHED_DATA_BY_DEFAULT)
    
    if events:
        logger.info(f"Retrieved {len(events)} events for the current weekend")
    else:
        logger.warning("No events found for the current weekend")


if __name__ == "__main__":
    main()
