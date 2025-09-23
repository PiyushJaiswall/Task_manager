import streamlit as st
from datetime import datetime
from supabase_client import fetch_transcripts, save_schedule, fetch_upcoming_reminders

st.set_page_config(page_title="BizExpress Meeting Dashboard", layout="wide")

st.title("BizExpress Meeting Dashboard")

# --- Login Form ---
with st.form("login_form"):
    user_email = st.text_input("Email")
    password = st.text_input("Password", type="password")  # optional password field
    login_submitted = st.form_submit_button("Login")

if login_submitted:
    if not user_email or not password:
        st.error("Please enter both email and password.")
    else:
        st.success(f"Logged in as {user_email}")

        # --- Display Meeting Summaries ---
        st.header("Meeting Summaries")
        transcripts = fetch_transcripts(user_email)
        if transcripts:
            for t in transcripts:
                st.subheader(t["meeting_title"])
                st.write(f"Start: {t['start_time']}, End: {t.get('end_time', 'N/A')}")
                st.write(t["transcript_text"])
        else:
            st.info("No transcripts available.")

        # --- Auto-Schedule Next Meeting ---
        st.header("Auto-Schedule Next Meeting")
        last_summary = transcripts[0]["transcript_text"] if transcripts else ""
        suggested_title = transcripts[0]["meeting_title"] + " - Follow up" if transcripts else "Next Meeting"
        suggested_time = datetime.now()

        with st.form("auto_schedule_form"):
            auto_meeting_title = st.text_input("Next Meeting Title", value=suggested_title)
            auto_date = st.date_input("Scheduled Date", value=suggested_time.date())
            auto_time = st.time_input("Scheduled Time", value=suggested_time.time())
            auto_notes = st.text_area("Notes", value=last_summary)
            auto_submitted = st.form_submit_button("Save Auto-Schedule")

            if auto_submitted:
                auto_scheduled_time = datetime.combine(auto_date, auto_time)
                save_schedule(user_email, auto_meeting_title, auto_scheduled_time.isoformat(), auto_notes)
                st.success("Auto-scheduled meeting saved!")

        # --- Manual Schedule Creation ---
        st.header("Create Manual Schedule")
        with st.form("manual_schedule_form"):
            manual_title = st.text_input("Meeting Title")
            manual_date = st.date_input("Scheduled Date", value=datetime.now().date())
            manual_time_input = st.time_input("Scheduled Time", value=datetime.now().time())
            manual_notes = st.text_area("Notes")
            manual_submitted = st.form_submit_button("Save Manual Schedule")

            if manual_submitted:
                manual_scheduled_time = datetime.combine(manual_date, manual_time_input)
                save_schedule(user_email, manual_title, manual_scheduled_time.isoformat(), manual_notes)
                st.success("Manual schedule saved!")

        # --- Upcoming Reminders ---
        st.header("Upcoming Reminders")
        try:
            reminders = fetch_upcoming_reminders(user_email)
            if reminders:
                for r in reminders:
                    st.write(f"{r['meeting_title']} at {r['scheduled_time']}")
            else:
                st.info("No upcoming reminders.")
        except Exception as e:
            st.error("Error fetching reminders. Check your Supabase setup.")
