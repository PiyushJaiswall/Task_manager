import streamlit as st
from transformers import pipeline
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from supabase import create_client, Client

# -----------------------------
# Load credentials from Streamlit secrets
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

EMAIL_FROM = st.secrets["EMAIL_FROM"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]

GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]

MS_TENANT_ID = st.secrets["MS_TENANT_ID"]
MS_CLIENT_ID = st.secrets["MS_CLIENT_ID"]
MS_CLIENT_SECRET = st.secrets["MS_CLIENT_SECRET"]

ZOOM_API_KEY = st.secrets["ZOOM_API_KEY"]
ZOOM_API_SECRET = st.secrets["ZOOM_API_SECRET"]

# -----------------------------
# Supabase client
# -----------------------------
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase connection failed: {e}")

# -----------------------------
# AI Summarizer
# -----------------------------
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# -----------------------------
# Helper functions
# -----------------------------
def mock_transcription():
    """Return a mock transcription for testing/demo purposes."""
    return "Mock transcription: Discussed Q4 targets, closed Acme deal at $50K."

def generate_summary(text):
    return summarizer(text, max_length=150, min_length=50, do_sample=False)[0]['summary_text']

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def schedule_reminder(event_time, reminder_text, email):
    def job():
        send_email(email, "BizExpress Reminder", reminder_text)
    schedule.every().day.at(event_time).do(job)

def save_note(content, note_type, user_email):
    data = {"content": content, "type": note_type, "user_email": user_email, "timestamp": datetime.now().isoformat()}
    supabase.table("notes").insert(data).execute()

def fetch_user_notes(user_email):
    response = supabase.table("notes").select("*").eq("user_email", user_email).execute()
    return response.data

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🛠️ BizExpress NoteForge")
tab1, tab2, tab3 = st.tabs(["Take Notes", "Summaries & Prep", "Reminders"])

# -----------------------------
# Tab 1: Take Notes
# -----------------------------
with tab1:
    st.header("Join & Take Notes")
    platform = st.selectbox("Platform", ["Google Meet", "Microsoft Teams", "Zoom"])
    meeting_link = st.text_input("Meeting Link/ID")
    user_email = st.text_input("Your Email")
    if st.button("Join & Transcribe"):
        st.info("Simulating join... Transcribing.")
        text = mock_transcription()  # Mock transcription instead of real audio
        save_note(text, "raw_notes", user_email)
        summary = generate_summary(text)
        st.success(f"Notes saved: {summary}")

# -----------------------------
# Tab 2: Summaries & Prep
# -----------------------------
with tab2:
    st.header("Generate Outputs")
    user_email = st.text_input("Your Email to fetch notes for summaries", key="summary_email")
    notes = fetch_user_notes(user_email) if user_email else []
    if notes:
        note_ids = [note["id"] for note in notes]
        note_id = st.selectbox("Select Note ID", note_ids)
        selected_note = next(n for n in notes if n["id"] == note_id)
        raw_text = selected_note["content"]
        if st.button("Create Summary"):
            summary = generate_summary(raw_text)
            st.write("**Summary:**", summary)
            send_email(user_email, "Meeting Summary", summary)
        if st.button("Create Prep Notes"):
            prep = generate_summary("Generate prep notes: " + raw_text)
            st.write("**Prep Notes:**", prep)
    else:
        st.info("No notes found for this email.")

# -----------------------------
# Tab 3: Reminders
# -----------------------------
with tab3:
    st.header("Set Reminders")
    event_desc = st.text_area("Event Description")
    reminder_time = st.time_input("Reminder Time")
    email = st.text_input("Send to Email")
    if st.button("Schedule"):
        reminder_text = f"Follow-up: {event_desc}"
        schedule_reminder(reminder_time.strftime("%H:%M"), reminder_text, email)
        st.success("Reminder scheduled!")

# -----------------------------
# Background Scheduler
# -----------------------------
if st.button("Start Reminder Engine"):
    st.info("Reminder engine running in background (Press Stop to end).")
    while True:
        schedule.run_pending()
        time.sleep(60)

st.info("App ready! Currently using mock transcription for demo purposes.")
