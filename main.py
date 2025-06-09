import logging
import time
import schedule
import threading
from datetime import datetime
from flask import Flask, jsonify, request
import os

from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, USE_CACHED_DATA_BY_DEFAULT
from data_processing.event_processing import get_current_weekend_events

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

# Initialize Flask app
app = Flask(__name__)

# Global variable to store latest events data
latest_events = []
last_update = None
scheduler_running = False


def scheduled_job():
    """Main job function for processing racing weather data."""
    global latest_events, last_update
    
    try:
        events = get_current_weekend_events(use_cached=USE_CACHED_DATA_BY_DEFAULT)
        
        if events:
            latest_events = events
            last_update = datetime.now()
            logger.info(f"Retrieved {len(events)} events for the current weekend")
        else:
            logger.warning("No events found for the current weekend")
            
    except Exception as e:
        logger.error(f"Error in scheduled job: {str(e)}")


def run_scheduler():
    """Run the scheduler in a separate thread."""
    global scheduler_running
    scheduler_running = True
    logger.info("Scheduler started, running job every 60 minutes")
    
    # Run job once immediately
    scheduled_job()
    
    # Schedule recurring job
    schedule.every(60).minutes.do(scheduled_job)
    
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)


# Flask Routes
@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        "message": "Racing Weather API is running!",
        "status": "healthy",
        "last_update": last_update.isoformat() if last_update else None,
        "events_count": len(latest_events)
    })


@app.route('/health')
def health_check():
    """Detailed health check."""
    return jsonify({
        "status": "healthy",
        "scheduler_running": scheduler_running,
        "last_update": last_update.isoformat() if last_update else None,
        "events_available": len(latest_events) > 0,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/events')
def get_events():
    """Get current weekend events."""
    try:
        # Option to force refresh
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if force_refresh:
            logger.info("Force refresh requested")
            scheduled_job()
        
        return jsonify({
            "events": latest_events,
            "count": len(latest_events),
            "last_update": last_update.isoformat() if last_update else None,
            "cached": not force_refresh
        })
        
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve events",
            "message": str(e)
        }), 500


@app.route('/api/events/refresh', methods=['POST'])
def refresh_events():
    """Manually trigger data refresh."""
    try:
        scheduled_job()
        return jsonify({
            "message": "Data refresh triggered successfully",
            "events_count": len(latest_events),
            "last_update": last_update.isoformat() if last_update else None
        })
        
    except Exception as e:
        logger.error(f"Error refreshing events: {str(e)}")
        return jsonify({
            "error": "Failed to refresh events",
            "message": str(e)
        }), 500


@app.route('/api/scheduler/status')
def scheduler_status():
    """Get scheduler status."""
    return jsonify({
        "scheduler_running": scheduler_running,
        "next_run": schedule.next_run().isoformat() if schedule.jobs else None,
        "jobs_count": len(schedule.jobs)
    })


@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler (useful for maintenance)."""
    global scheduler_running
    scheduler_running = False
    schedule.clear()
    logger.info("Scheduler stopped")
    
    return jsonify({
        "message": "Scheduler stopped successfully",
        "scheduler_running": scheduler_running
    })


@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler."""
    global scheduler_running
    
    if not scheduler_running:
        # Start scheduler in a new thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return jsonify({
            "message": "Scheduler started successfully",
            "scheduler_running": scheduler_running
        })
    else:
        return jsonify({
            "message": "Scheduler is already running",
            "scheduler_running": scheduler_running
        })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)