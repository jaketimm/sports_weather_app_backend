import logging
import time
import schedule
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, USE_CACHED_DATA_BY_DEFAULT
from data_processing.event_processing import get_current_weekend_events

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        # logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def job():
    """Main entry point for the racing weather application."""
    events = get_current_weekend_events(use_cached=USE_CACHED_DATA_BY_DEFAULT)

    if events:
        logger.info(f"Retrieved {len(events)} events for the current weekend")
    else:
        logger.warning("No events found for the current weekend")


if __name__ == "__main__":
    schedule.every(60).minutes.do(job)

    logger.info("Scheduler started, running job every 30 minutes")
    while True:
        schedule.run_pending()
        time.sleep(1)
