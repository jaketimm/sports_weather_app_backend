import logging
from racing_weather_api.config import LOG_FILE, LOG_LEVEL, LOG_FORMAT
from wilson_ave_river_data_api.river_data_updater import update_wilson_ave_river_data

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
    update_wilson_ave_river_data()
    
except Exception as e:
    logger.error(f"Error in scheduled job: {str(e)}")

