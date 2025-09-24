# supabase_client.py
from supabase import create_client, Client
import os
from datetime import datetime

# --- Supabase credentials from environment variables ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Fetch meeting transcripts ---
def fetch_transcripts(user_email: str):
    try:
        response = supabase.table("meeting_transcripts")\
            .select("*")\
            .eq("user_email", user_email)\
            .order("start_time", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Error fetching transcripts: {e}")
        return []

# --- Save schedule (manual or auto) ---
def save_schedule(user_email: str, meeting_title: str, scheduled_time: str, notes: str = "", reminder_time: str = None):
    data = {
        "user_email": user_email,
        "meeting_title": meeting_title,
        "scheduled_time": scheduled_time,
        "notes": notes,
        "reminder_time": reminder_time,
        "reminder_sent": False
    }
    try:
        response = supabase.table("meeting_schedules").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Error saving schedule: {e}")
        return []

# --- Fetch upcoming reminders ---
def fetch_upcoming_reminders(user_email: str):
    now = datetime.utcnow().isoformat()
    try:
        response = supabase.table("meeting_schedules")\
            .select("*")\
            .eq("user_email", user_email)\
            .gte("reminder_time", now)\
            .eq("reminder_sent", False)\
            .order("reminder_time", asc=True)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Error fetching reminders: {e}")
        return []

def delete_transcript(transcript_id: int):
    try:
        supabase.table("meeting_transcripts").delete().eq("id", transcript_id).execute()
    except Exception as e:
        print(f"Error deleting transcript: {e}")

def delete_schedule(schedule_id: int):
    try:
        supabase.table("meeting_schedules").delete().eq("id", schedule_id).execute()
    except Exception as e:
        print(f"Error deleting schedule: {e}")

