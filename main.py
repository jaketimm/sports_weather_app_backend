import logging
from racing_weather_api.config import LOG_FILE, LOG_LEVEL, LOG_FORMAT
from racing_weather_api.data_processing.event_processing import get_events_with_weather

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Enable for production deployment
    ]
)
logger = logging.getLogger(__name__)


try:
    events = get_events_with_weather(use_cached=False)

    if events:
        logger.info(f"Retrieved {len(events)} events for the current weekend")
    else:
        logger.warning("No events found for the current weekend")
    
except Exception as e:
    logger.error(f"Error in scheduled job: {str(e)}")

