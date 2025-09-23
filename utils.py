# You can add any helper functions here, e.g., formatting dates, filtering reminders, etc.
from datetime import datetime

def format_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%Y-%m-%d %H:%M")
