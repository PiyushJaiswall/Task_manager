import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import schedule
import time
from datetime import datetime
from supabase import create_client
import smtplib
from email.mime.text import MIMEText

# ---------------------------
# Streamlit Secrets
# ---------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------
# Summarizer
# ---------------------------
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ---------------------------
# Credentials Input Sidebar
# ---------------------------
st.sidebar.header("🔐 Credentials & API Keys")

if "credentials_set" not in st.session_state:
    st.session_state["EMAIL_FROM"] = st.sidebar.text_input("Email From")
    st.session_state["EMAIL_PASSWORD"] = st.sidebar.text_input("Email Password (App Password)", type="password")
    st.session_state["GOOGLE_CLIENT_ID"] = st.sidebar.text_input("Google Client ID")
    st.session_state["GOOGLE_CLIENT_SECRET"] = st.sidebar.text_input("Google Client Secret")
    st.session_state["MS_TENANT_ID"] = st.sidebar.text_input("Microsoft Tenant ID")
    st.session_state["MS_CLIENT_ID"] = st.sidebar.text_input("Microsoft Client ID")
    st.session_state["MS_CLIENT_SECRET"] = st.sidebar.text_input("Microsoft Client Secret")
    st.session_state["ZOOM_API_KEY"] = st.sidebar.text_input("Zoom API Key")
    st.session_state["ZOOM_API_SECRET"] = st.sidebar.text_input("Zoom API Secret")
    
    if st.sidebar.button("Save Credentials"):
        st.session_state["credentials_set"] = True
        st.success("Credentials saved for this session!")
else:
    st.sidebar.success("Credentials are set!")

# ---------------------------
# Functions
# ---------------------------
def transcribe_audio(audio_file):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        return r.recognize_google(audio)
    except:
        return "Mock transcription: Discussed Q4 targets, closed Acme deal at $50K."

def generate_summary(text):
    return summarizer(text, max_length=150, min_length=50, do_sample=False)[0]['summary_text']

def send_email(to_email, subject, body):
    EMAIL_FROM = st.session_state.get("EMAIL_FROM")
    EMAIL_PASSWORD = st.session_state.get("EMAIL_PASSWORD")
    
    if not EMAIL_FROM or not EMAIL_PASSWORD:
        st.error("Please set your email credentials in the sidebar first.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success(f"Email sent to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def schedule_reminder(event_time, reminder_text, email):
    def job():
        send_email(email, "BizExpress Reminder", reminder_text)
    schedule.every().day.at(event_time).do(job)

def save_note_to_supabase(user_email, text, note_type="raw_notes"):
    supabase.table("notes").insert({
        "user_email": user_email,
        "timestamp": datetime.now().isoformat(),
        "content": text,
        "type": note_type
    }).execute()

def fetch_user_notes(user_email):
    data = supabase.table("notes").select("*").eq("user_email", user_email).execute()
    return data.data if data.data else []

# ---------------------------
# Main UI
# ---------------------------
st.title("🛠️ BizExpress NoteForge")

tab1, tab2, tab3 = st.tabs(["Take Notes", "Summaries & Prep", "Reminders"])

user_email = st.session_state.get("EMAIL_FROM", "guest@example.com")

# ---------------------------
# Tab 1: Take Notes
# ---------------------------
with tab1:
    platform = st.selectbox("Platform", ["Google Meet", "Microsoft Teams", "Zoom"])
    meeting_link = st.text_input("Meeting Link/ID")
    if st.button("Join & Transcribe"):
        st.info("Simulating join... Transcribing.")
        text = transcribe_audio("fixed_audio.wav")
        summary = generate_summary(text)
        save_note_to_supabase(user_email, text)
        st.success(f"Notes saved: {summary}")

# ---------------------------
# Tab 2: Summaries & Prep
# ---------------------------
with tab2:
    notes = fetch_user_notes(user_email)
    if notes:
        note_options = {f"{n['timestamp']}": n['content'] for n in notes}
        selected_time = st.selectbox("Select Note by Timestamp", list(note_options.keys()))
        raw_text = note_options[selected_time]

        if st.button("Create Summary"):
            summary = generate_summary(raw_text)
            st.write("**Summary:**", summary)
            send_email(user_email, "Meeting Summary", summary)

        if st.button("Create Prep Notes"):
            prep = generate_summary("Generate prep notes: " + raw_text)
            st.write("**Prep Notes:**", prep)
    else:
        st.info("No notes found yet. Take notes first in Tab 1.")

# ---------------------------
# Tab 3: Reminders
# ---------------------------
with tab3:
    event_desc = st.text_area("Event Description")
    reminder_time = st.time_input("Reminder Time")
    email_to = st.text_input("Send to Email")
    if st.button("Schedule"):
        reminder_text = f"Follow-up: {event_desc}"
        schedule_reminder(reminder_time.strftime("%H:%M"), reminder_text, email_to)
        st.success("Reminder scheduled!")

# ---------------------------
# Reminder Engine
# ---------------------------
if st.button("Start Reminder Engine"):
    while True:
        schedule.run_pending()
        time.sleep(60)



