import requests

url = 'http://67.205.133.211/data/events_with_weather.json'  # Using Public IP
output_file = 'events_with_weather.json'

response = requests.get(url)

# Optional: check for successful response
if response.status_code == 200:
    with open(output_file, 'wb') as f:
        f.write(response.content)
    print("File downloaded successfully.")
else:
    print(f"Failed to download file. HTTP Status: {response.status_code}")
