## Description

This project is a Python application parses racing event schedules, retrieves weather data for track locations, and saves it
to a JSON file. It uses the Google Weather API to fetch and process weather and location data.

## Features

- Parse racing schedules from PDF or JSON data
- Fetch weather forecasts for specific tracks
- Process maps API data for locations

## Requirements

- Python 3.x
- Required libraries: PyQt5 requests python-dotenv

## Installation

1. Clone the repository:
   ```
   git clone <repo-url>
   cd sports_weather_app
   ```

2. Install dependencies:
   ```
   pip install PyQt5 requests python-dotenv
   ```

## Environment Setup

### Creating a .env File

This project uses environment variables for sensitive information like API keys. Create a `.env` file in the root directory of the project.

1. Create a new .env file:
   ```
   touch .env
   ```

2. Add the necessary variables. 
   ```
   MAPSAPI_KEY="your_api_key_here"
   ```

### Getting a Google Weather API Key

1. Visit: [https://console.cloud.google.com/marketplace/product/google/weather.googleapis.com](https://console.cloud.google.com/marketplace/product/google/weather.googleapis.com)
2. Enable the Weather API for your project.
3. Create an API key in the credentials section.
4. Add the key to your `.env` file as `MAPSAPI_KEY`.

## Usage

1. Run the main application:
   ```
   python main.py
   ```

