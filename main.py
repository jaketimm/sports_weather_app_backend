# main.py
import sys
from data_processing.data_processing import get_current_weekend_events

def main():

    # Fetch new data from API (this will save to file)
    events = get_current_weekend_events(use_cached=False)

if __name__ == "__main__":
    main()