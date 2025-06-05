import pdfplumber
import re
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Extract text from Nascar Schedule PDF
def extract_text_from_pdf():
    with pdfplumber.open("data/2025-NationalSeriesSchedule-Networks.pdf") as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()

        return text

# Parse PDF text into weekends (Fri - Sun)
def parse_schedule(text, year=2025):
    month_map = {
        'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6,
        'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10, 'NOV':11, 'DEC':12
    }

    pattern = re.compile(
        r"(?P<location>[A-Z0-9\*\.\(\) ]+?)\s(?P<day_of_week>FRI|SAT|SUN)\s\|\s(?P<month>[A-Z]{3})\s(?P<day>\d{1,2})\s\|\s(?P<time>\d{1,2}(?::\d{2})?\s[AP]M)\s\|\s(?P<channel>[A-Z0-9]+)"
    )

    def get_date(month_str, day):
        month = month_map[month_str]
        return datetime(year, month, int(day))

    def get_weekend_friday(date, weekday_str):
        weekday_map = {'MON':0, 'TUE':1, 'WED':2, 'THU':3, 'FRI':4, 'SAT':5, 'SUN':6}
        day_num = weekday_map[weekday_str]
        days_to_friday = (day_num - 4) % 7
        friday_date = date - timedelta(days=days_to_friday)
        return friday_date

    matches = pattern.finditer(text)
    events_by_weekend = defaultdict(list)

    for m in matches:
        location = m.group('location').strip().replace('*', '')
        dow = m.group('day_of_week')
        month = m.group('month')
        day = m.group('day')
        time = m.group('time')
        channel = m.group('channel')

        event_date = get_date(month, day)
        weekend_friday = get_weekend_friday(event_date, dow)

        event_info = {
            'Series': 'NASCAR',
            'location': location,
            'day_of_week': dow,
            'date': event_date.strftime("%Y-%m-%d"),
            'time': time,
            'channel': channel
        }

        events_by_weekend[weekend_friday].append(event_info)

    return events_by_weekend


# Convert weekends to JSON-serializable format
def weekends_to_json(weekends, output_file="data/schedule.json"):
    json_ready = {
        friday.strftime("%Y-%m-%d"): events
        for friday, events in weekends.items()
    }

    with open(output_file, "w") as f:
        json.dump(json_ready, f, indent=2)


# Extract schedule from nascar.com PDF, save to schedule.json
text = extract_text_from_pdf()
weekends = parse_schedule(text)
weekends_to_json(weekends)