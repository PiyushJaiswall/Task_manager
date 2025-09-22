import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import schedule
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import config

# Summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# DB Setup
conn = sqlite3.connect('bizexpress_notes.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, timestamp TEXT, content TEXT, type TEXT)''')
conn.commit()

# Functions
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
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config.EMAIL_FROM
    msg['To'] = to_email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
        server.send_message(msg)

def schedule_reminder(event_time, reminder_text, email):
    def job():
        send_email(email, "BizExpress Reminder", reminder_text)
    schedule.every().day.at(event_time).do(job)

# Streamlit UI
st.title("🛠️ BizExpress NoteForge")
tab1, tab2, tab3 = st.tabs(["Take Notes", "Summaries & Prep", "Reminders"])

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

with tab3:
    event_desc = st.text_area("Event Description")
    reminder_time = st.time_input("Reminder Time")
    email = st.text_input("Send to Email")
    if st.button("Schedule"):
        reminder_text = f"Follow-up: {event_desc}"
        schedule_reminder(reminder_time.strftime("%H:%M"), reminder_text, email)
        st.success("Reminder scheduled!")

if st.button("Start Reminder Engine"):
    while True:
        schedule.run_pending()
        time.sleep(60)
