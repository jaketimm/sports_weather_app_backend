# Description

This project is a Python codebase that contains 3 data APIs.

## Racing Weather API:

- Uses the Google Weather API to fetch and process weather data for motorsports events.
- Creates a 5 hour event forecast for all events in a rolling 7 day window
- Output data is saved at var/www/html/data/events_with_weather.json and var/www/html/data/all_10_day_forecasts.json
- Updates data every hour

- Schedule data is compiled manually and stored in racing_weather_api/data/series_schedules (All start times are in EST). Start times are converted to UTC when retrieving event weather data.
