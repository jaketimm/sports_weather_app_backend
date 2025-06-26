# Description

This project is a Python codebase that contains 3 data APIs.

## 1) Racing Weather API:

- parses racing event schedules and retrieves weather data for track locations. It uses the Google Weather API to fetch and process weather and location data.
Schedule data is compiled manually and stored in racing_weather_api/data/series_schedules
- Runs a scheduled job every hour
- Processes events in a rolling 7 day window
- Fetches weather forecasts for specific tracks
- Process maps weather API data to create a 5 hour forecast window for each event
- Output data is saved at var/www/html/data/events_with_weather.json and var/www/html/data/all_10_day_forecasts.json

## 2) Wilson Ave River Data API

- Downloads 6 hours of river data from the USGS and appends it to var/www/html/data/river_data_m-11.csv
- Runs a scheduled job every 6 hours

## 3) NOAA Buoy Data API

- under construction