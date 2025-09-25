# supabase_client.py
from supabase import create_client, Client
import os
from datetime import datetime
import io
import csv

# --- Supabase credentials from environment variables ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Authentication ---
def sign_in(email: str, password: str):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return user.user is not None
    except Exception as e:
        print(f"Login error: {e}")
        return False

def sign_up(email: str, password: str):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        return user.user is not None
    except Exception as e:
        print(f"Signup error: {e}")
        return False

# --- Fetch meeting transcripts (your existing function) ---
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

# --- Save schedule (your existing function) ---
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

# --- Fetch upcoming reminders (your existing function) ---
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

# --- Delete functions (your existing functions) ---
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

# === NEW FUNCTIONS FOR MEETING TRANSCRIPT MANAGER ===

# --- Meeting and Transcript Management Functions ---

def fetch_meetings():
    """Fetch all meetings with their associated transcript info"""
    try:
        response = supabase.table("meetings")\
            .select("*, transcripts(meeting_title, audio_url)")\
            .order("created_at", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Error fetching meetings: {e}")
        return []

def fetch_meeting_by_id(meeting_id: str):
    """Fetch a specific meeting by ID"""
    try:
        response = supabase.table("meetings")\
            .select("*")\
            .eq("id", meeting_id)\
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching meeting: {e}")
        return None

def create_new_meeting(title: str, summary: str, key_points: list, followup_points: list, next_meet_schedule: str = None, transcript_id: str = None):
    """Create a new meeting record - NEW FUNCTION for manual meeting creation"""
    try:
        new_meeting_data = {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "followup_points": followup_points
        }

        if next_meet_schedule:
            new_meeting_data["next_meet_schedule"] = next_meet_schedule

        if transcript_id:
            new_meeting_data["transcript_id"] = transcript_id

        response = supabase.table("meetings").insert(new_meeting_data).execute()
        return True
    except Exception as e:
        print(f"Error creating meeting: {e}")
        return False

def update_meeting(meeting_id: str, title: str, summary: str, key_points: list, followup_points: list, next_meet_schedule: str = None):
    """Update a meeting record"""
    try:
        update_data = {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "followup_points": followup_points
        }

        if next_meet_schedule:
            update_data["next_meet_schedule"] = next_meet_schedule

        response = supabase.table("meetings")\
            .update(update_data)\
            .eq("id", meeting_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Error updating meeting: {e}")
        return False

def fetch_transcript_by_id(transcript_id: str):
    """Fetch transcript by ID"""
    try:
        response = supabase.table("transcripts")\
            .select("*")\
            .eq("id", transcript_id)\
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def get_database_stats():
    """Get database statistics"""
    try:
        # Get meetings count
        meetings_response = supabase.table("meetings").select("id", count="exact").execute()
        meetings_count = meetings_response.count or 0

        # Get transcripts count  
        transcripts_response = supabase.table("transcripts").select("id", count="exact").execute()
        transcripts_count = transcripts_response.count or 0

        # Note: Supabase doesn't provide direct table size info via client
        # These would need to be calculated or estimated based on content
        # For now, providing basic stats

        return {
            "meetings_count": meetings_count,
            "transcripts_count": transcripts_count,
            "meetings_size_mb": meetings_count * 0.01,  # Rough estimate
            "transcripts_size_mb": transcripts_count * 0.05,  # Rough estimate  
            "total_size_mb": (meetings_count * 0.01) + (transcripts_count * 0.05)
        }
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {
            "meetings_count": 0,
            "transcripts_count": 0,
            "meetings_size_mb": 0,
            "transcripts_size_mb": 0,
            "total_size_mb": 0
        }

def delete_old_records(cutoff_date: str):
    """Delete records older than cutoff_date"""
    try:
        # Delete old meetings
        meetings_response = supabase.table("meetings")\
            .delete()\
            .lt("created_at", cutoff_date)\
            .execute()

        # Delete old transcripts
        transcripts_response = supabase.table("transcripts")\
            .delete()\
            .lt("transcript_created_at", cutoff_date)\
            .execute()

        # Return count of deleted records (this is approximate)
        return len(meetings_response.data or []) + len(transcripts_response.data or [])

    except Exception as e:
        print(f"Error deleting old records: {e}")
        return 0

def export_meetings_csv(start_date: str, end_date: str):
    """Export meetings data as CSV for date range"""
    try:
        response = supabase.table("meetings")\
            .select("*, transcripts(meeting_title)")\
            .gte("created_at", start_date)\
            .lte("created_at", end_date)\
            .order("created_at", desc=True)\
            .execute()

        if not response.data:
            return None

        # Convert to CSV format
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = ["ID", "Title", "Summary", "Key Points", "Followup Points", 
                  "Next Meeting", "Created At", "Updated At", "Original Meeting Title", "Source Type"]
        writer.writerow(headers)

        # Write data
        for meeting in response.data:
            key_points_str = "; ".join(meeting.get("key_points") or [])
            followup_str = "; ".join(meeting.get("followup_points") or [])
            original_title = ""
            source_type = "Manual Entry"

            if meeting.get("transcripts"):
                original_title = meeting["transcripts"].get("meeting_title", "")
                source_type = "From Transcript"

            writer.writerow([
                meeting.get("id", ""),
                meeting.get("title", ""),
                meeting.get("summary", ""),
                key_points_str,
                followup_str,
                meeting.get("next_meet_schedule", ""),
                meeting.get("created_at", ""),
                meeting.get("updated_at", ""),
                original_title,
                source_type
            ])

        return output.getvalue()

    except Exception as e:
        print(f"Error exporting meetings: {e}")
        return None
