"""
Utility functions for file operations and JSON handling.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

def load_json(file_path: str):
    """Load JSON from file, return dict or None on error."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading JSON: {e}")  
        return None


def save_json(data, file_path: str):
    """Save data to a JSON file."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False
