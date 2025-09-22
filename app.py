import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import schedule
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ---------------------------
# Summarizer
# ---------------------------
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ---------------------------
# DB Setup
# ---------------------------
conn = sqlite3.connect('bizexpress_notes.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, timestamp TEXT, content TEXT, type TEXT)''')
conn.commit()

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
        st.error("Please set your email credentials in the Credentials tab first.")
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

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🛠️ BizExpress NoteForge")

# ---------------------------
# Credentials input
# ---------------------------
st.sidebar.header("Credentials (Email/API)")
if "credentials_set" not in st.session_state:
    st.session_state["EMAIL_FROM"] = st.sidebar.text_input("Email From")
    st.session_state["EMAIL_PASSWORD"] = st.sidebar.text_input("Email Password (app password)", type="password")
    if st.sidebar.button("Save Credentials"):
        st.session_state["credentials_set"] = True
        st.success("Credentials saved for this session!")
else:
    st.sidebar.success("Credentials are set!")

# ---------------------------
# Tabs
# ---------------------------
tab1, tab2, tab3 = st.tabs(["Take Notes", "Summaries & Prep", "Reminders"])

# ---------------------------
# Tab 1: Take Notes
# ---------------------------
with tab1:
    platform = st.selectbox("Platform", ["Google Meet", "Microsoft Teams", "Zoom"])
    meeting_link = st.text_input("Meeting Link/ID")
    if st.button("Join & Transcribe"):
        st.info("Simulating join... Transcribing.")
        text = transcribe_audio("mock_audio.wav")
        summary = generate_summary(text)
        c.execute("INSERT INTO notes VALUES (NULL, ?, ?, ?)", (datetime.now().isoformat(), text, "raw_notes"))
        conn.commit()
        st.success(f"Notes saved: {summary}")

# ---------------------------
# Tab 2: Summaries & Prep
# ---------------------------
with tab2:
    note_id = st.number_input("Note ID from DB", min_value=1)
    c.execute("SELECT content FROM notes WHERE id=?", (note_id,))
    row = c.fetchone()
    raw_text = row[0] if row else "No notes found."
    if st.button("Create Summary"):
        summary = generate_summary(raw_text)
        st.write("**Summary:**", summary)
        send_email("user@bizexpress.com", "Meeting Summary", summary)
    if st.button("Create Prep Notes"):
        prep = generate_summary("Generate prep notes: " + raw_text)
        st.write("**Prep Notes:**", prep)

# ---------------------------
# Tab 3: Reminders
# ---------------------------
with tab3:
    event_desc = st.text_area("Event Description")
    reminder_time = st.time_input("Reminder Time")
    email = st.text_input("Send to Email")
    if st.button("Schedule"):
        reminder_text = f"Follow-up: {event_desc}"
        schedule_reminder(reminder_time.strftime("%H:%M"), reminder_text, email)
        st.success("Reminder scheduled!")

# ---------------------------
# Background scheduler
# ---------------------------
if st.button("Start Reminder Engine"):
    while True:
        schedule.run_pending()
        time.sleep(60)
