from supabase import create_client, Client
import os
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch meeting transcripts
def fetch_transcripts(user_email: str):
    response = supabase.table("meeting_transcripts")\
        .select("*")\
        .eq("user_email", user_email)\
        .order("start_time", desc=True)\
        .execute()
    return response.data

# Save schedule (manual or auto)
def save_schedule(user_email: str, meeting_title: str, scheduled_time: str, notes: str = "", reminder_time: str = None):
    data = {
        "user_email": user_email,
        "meeting_title": meeting_title,
        "scheduled_time": scheduled_time,
        "notes": notes,
        "reminder_time": reminder_time,
        "reminder_sent": False
    }
    response = supabase.table("meeting_schedules").insert(data).execute()
    return response.data

# Fetch upcoming reminders
def fetch_upcoming_reminders(user_email: str):
    now = datetime.utcnow().isoformat()
    response = supabase.table("meeting_schedules")\
        .select("*")\
        .eq("user_email", user_email)\
        .lt("reminder_time", now)\
        .eq("reminder_sent", False)\
        .execute()
    return response.data
