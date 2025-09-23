import streamlit as st
from datetime import datetime, timedelta
from supabase_client import fetch_transcripts, save_schedule, fetch_upcoming_reminders

st.set_page_config(page_title="BizExpress Meeting Dashboard", layout="wide")
st.title("BizExpress Meeting Dashboard")

# --- Login Form ---
with st.form("login_form"):
    user_email = st.text_input("Email")
    user_password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    if not user_email or not user_password:
        st.error("Please enter both email and password")
    else:
        st.success(f"Logged in as {user_email}")

        # --- Display Meeting Summaries ---
        st.header("Meeting Summaries")
        transcripts = fetch_transcripts(user_email)
        if transcripts:
            for t in transcripts:
                st.markdown(f"**Title:** {t.get('meeting_title')}")
                st.markdown(f"**Summary:** {t.get('summary')}")
                st.markdown(f"**Start Time:** {t.get('start_time')}")
                st.markdown("---")
        else:
            st.info("No transcripts available.")

        # --- Auto-Schedule Next Meeting ---
        st.header("Auto-Schedule Next Meeting")
        last_summary = transcripts[0]['summary'] if transcripts else ""
        suggested_title = f"Follow-up: {last_summary[:30]}..." if last_summary else ""
        suggested_time = datetime.now() + timedelta(days=7)  # Default 7 days later

        with st.form("auto_schedule_form"):
            auto_meeting_title = st.text_input("Next Meeting Title", value=suggested_title)
            auto_scheduled_time = st.datetime_input("Scheduled Time", value=suggested_time)
            auto_notes = st.text_area("Notes", value=last_summary)
            auto_submitted = st.form_submit_button("Save Auto-Schedule")

            if auto_submitted:
                save_schedule(user_email, auto_meeting_title, auto_scheduled_time.isoformat(), auto_notes)
                st.success("Auto-scheduled meeting saved!")

        # --- Manual Schedule Creation ---
        st.header("Create Manual Schedule")
        with st.form("manual_schedule_form"):
            manual_title = st.text_input("Meeting Title")
            manual_time = st.datetime_input("Scheduled Time", value=datetime.now())
            manual_notes = st.text_area("Notes")
            manual_submitted = st.form_submit_button("Save Manual Schedule")

            if manual_submitted:
                save_schedule(user_email, manual_title, manual_time.isoformat(), manual_notes)
                st.success("Manual schedule saved!")

        # --- Upcoming Reminders ---
        st.header("Upcoming Reminders")
        try:
            reminders = fetch_upcoming_reminders(user_email)
            if reminders:
                for r in reminders:
                    st.markdown(f"**Title:** {r.get('meeting_title')}")
                    st.markdown(f"**Scheduled Time:** {r.get('scheduled_time')}")
                    st.markdown(f"**Reminder Time:** {r.get('reminder_time')}")
                    st.markdown("---")
            else:
                st.info("No upcoming reminders.")
        except Exception as e:
            st.error(f"Error fetching reminders: {e}")
