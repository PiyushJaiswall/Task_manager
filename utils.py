import re
import pandas as pd
from datetime import datetime, timedelta
import json

def format_date(date_string):
    """Format date string to a readable format"""
    try:
        date_obj = pd.to_datetime(date_string)
        return date_obj.strftime('%Y-%m-%d %H:%M')
    except:
        return date_string

def truncate_text(text, max_length=50):
    """Truncate text to specified length"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def extract_keywords(text, num_keywords=5):
    """Extract keywords from text using simple word frequency"""
    if not text:
        return []

    # Simple keyword extraction
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = {}

    # Common words to ignore
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'a', 'an', 'this', 'that', 'these', 'those'}

    for word in words:
        if len(word) > 3 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency and return top keywords
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [keyword for keyword, freq in sorted_keywords[:num_keywords]]

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_reading_time(text):
    """Calculate estimated reading time for text"""
    if not text:
        return 0

    # Average reading speed: 200 words per minute
    word_count = len(text.split())
    reading_time = word_count / 200
    return max(1, round(reading_time))

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

def get_date_range_options():
    """Get predefined date range options"""
    today = datetime.now().date()

    return {
        "Today": (today, today),
        "Yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        "This Week": (today - timedelta(days=today.weekday()), today),
        "Last Week": (
            today - timedelta(days=today.weekday() + 7),
            today - timedelta(days=today.weekday() + 1)
        ),
        "This Month": (today.replace(day=1), today),
        "Last Month": get_last_month_range(today),
        "Last 30 Days": (today - timedelta(days=30), today),
        "Last 90 Days": (today - timedelta(days=90), today)
    }

def get_last_month_range(current_date):
    """Get first and last day of previous month"""
    if current_date.month == 1:
        last_month_year = current_date.year - 1
        last_month = 12
    else:
        last_month_year = current_date.year
        last_month = current_date.month - 1

    first_day = current_date.replace(year=last_month_year, month=last_month, day=1)

    # Get last day of the month
    if last_month == 12:
        next_month_first = current_date.replace(year=last_month_year + 1, month=1, day=1)
    else:
        next_month_first = current_date.replace(year=last_month_year, month=last_month + 1, day=1)

    last_day = next_month_first - timedelta(days=1)

    return (first_day, last_day)

def sanitize_filename(filename):
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Truncate if too long
    if len(filename) > 100:
        filename = filename[:100]

    return filename.strip()

def parse_meeting_data(raw_data):
    """Parse and validate meeting data"""
    parsed_data = {}

    # Required fields
    parsed_data['title'] = raw_data.get('title', '').strip()
    parsed_data['summary'] = raw_data.get('summary', '').strip()

    # Array fields
    key_points = raw_data.get('key_points', [])
    if isinstance(key_points, str):
        key_points = [key_points]
    parsed_data['key_points'] = [point.strip() for point in key_points if point.strip()]

    followup_points = raw_data.get('followup_points', [])
    if isinstance(followup_points, str):
        followup_points = [followup_points]
    parsed_data['followup_points'] = [point.strip() for point in followup_points if point.strip()]

    # Optional fields
    parsed_data['next_meet_schedule'] = raw_data.get('next_meet_schedule')
    parsed_data['transcript_id'] = raw_data.get('transcript_id')

    return parsed_data

def validate_meeting_data(meeting_data):
    """Validate meeting data before saving"""
    errors = []

    if not meeting_data.get('title'):
        errors.append("Meeting title is required")

    if not meeting_data.get('summary'):
        errors.append("Meeting summary is required")

    if len(meeting_data.get('title', '')) > 200:
        errors.append("Meeting title is too long (max 200 characters)")

    if len(meeting_data.get('summary', '')) > 5000:
        errors.append("Meeting summary is too long (max 5000 characters)")

    return errors

def generate_export_filename(start_date, end_date, file_type="csv"):
    """Generate filename for data export"""
    start_str = start_date.strftime('%Y%m%d') if isinstance(start_date, datetime) else str(start_date).replace('-', '')
    end_str = end_date.strftime('%Y%m%d') if isinstance(end_date, datetime) else str(end_date).replace('-', '')

    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"meetings_export_{start_str}_to_{end_str}_{timestamp}.{file_type}"

    return sanitize_filename(filename)

class MeetingSearchFilter:
    """Class to handle meeting search and filtering"""

    @staticmethod
    def search_meetings(meetings, query):
        """Search meetings by title, summary, and key points"""
        if not query:
            return meetings

        query = query.lower()
        filtered = []

        for meeting in meetings:
            # Search in title
            if query in meeting.get('title', '').lower():
                filtered.append(meeting)
                continue

            # Search in summary
            if query in meeting.get('summary', '').lower():
                filtered.append(meeting)
                continue

            # Search in key points
            key_points = meeting.get('key_points', [])
            if any(query in point.lower() for point in key_points):
                filtered.append(meeting)
                continue

            # Search in followup points
            followup_points = meeting.get('followup_points', [])
            if any(query in point.lower() for point in followup_points):
                filtered.append(meeting)
                continue

        return filtered

    @staticmethod
    def filter_by_date(meetings, start_date, end_date):
        """Filter meetings by date range"""
        if not start_date or not end_date:
            return meetings

        filtered = []
        for meeting in meetings:
            meeting_date = pd.to_datetime(meeting['created_at']).date()
            if start_date <= meeting_date <= end_date:
                filtered.append(meeting)

        return filtered

    @staticmethod
    def filter_by_source(meetings, source_type):
        """Filter meetings by source type (manual/automatic)"""
        if not source_type or source_type.lower() == 'all':
            return meetings

        filtered = []
        for meeting in meetings:
            has_transcript = bool(meeting.get('transcript_id'))
            meeting_source = 'automatic' if has_transcript else 'manual'

            if source_type.lower() == meeting_source:
                filtered.append(meeting)

        return filtered

def create_meeting_summary_stats(meetings):
    """Create summary statistics for meetings"""
    if not meetings:
        return {}

    total_meetings = len(meetings)
    manual_meetings = sum(1 for m in meetings if not m.get('transcript_id'))
    automatic_meetings = total_meetings - manual_meetings

    # Date range
    dates = [pd.to_datetime(m['created_at']).date() for m in meetings]
    earliest_date = min(dates)
    latest_date = max(dates)

    # Average key points
    total_key_points = sum(len(m.get('key_points', [])) for m in meetings)
    avg_key_points = total_key_points / total_meetings if total_meetings > 0 else 0

    return {
        'total_meetings': total_meetings,
        'manual_meetings': manual_meetings,
        'automatic_meetings': automatic_meetings,
        'date_range': f"{earliest_date} to {latest_date}",
        'average_key_points': round(avg_key_points, 1)
    }
