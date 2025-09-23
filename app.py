import streamlit as st
from supabase_client import fetch_transcripts, save_schedule, fetch_upcoming_reminders
from datetime import datetime, timedelta

st.set_page_config(page_title="BizExpress Meetings", layout="wide")
st.title("BizExpress Meeting Dashboard")

# User login/email
user_email = st.text_input("Enter your email", "")

if user_email:
    # --- Display Meeting Summaries ---
    st.subheader("Meeting Summaries")
    transcripts = fetch_transcripts(user_email)
    if transcripts:
        for t in transcripts:
            st.markdown(f"**{t['meeting_name']}** ({t['start_time']} - {t['end_time']})")
            st.markdown(f"{t['transcript_text'][:300]}...")  # show first 300 chars
            st.markdown("---")
    else:
        st.info("No transcripts available.")

    # --- Manual Schedule ---
    st.subheader("Create Manual Schedule")
    with st.form("manual_schedule_form"):
        meeting_title = st.text_input("Meeting Title")
        scheduled_time = st.datetime_input("Scheduled Time", datetime.now())
        notes = st.text_area("Notes / Summary")
        reminder_time = st.datetime_input("Reminder Time", datetime.now() + timedelta(hours=1))
        submitted = st.form_submit_button("Save Schedule")
        if submitted:
            save_schedule(
                user_email, 
                meeting_title, 
                scheduled_time.isoformat(), 
                notes, 
                reminder_time.isoformat()
            )
            st.success("Schedule saved!")

    # --- Auto-Schedule Next Meeting ---
    st.subheader("Auto-Schedule Next Meeting")
    if transcripts:
        last_meeting = transcripts[0]
        next_time = datetime.fromisoformat(last_meeting['end_time']) + timedelta(days=1)
        st.markdown(f"Suggested Next Meeting: {next_time.strftime('%Y-%m-%d %H:%M')}")
        if st.button("Save Auto-Schedule"):
            save_schedule(
                user_email,
                f"Follow-up: {last_meeting['meeting_name']}",
                next_time.isoformat(),
                last_meeting['transcript_text']
            )
            st.success("Auto-schedule saved!")

    # --- Reminders ---
    st.subheader("Upcoming Reminders")
    reminders = fetch_upcoming_reminders(user_email)
    if reminders:
        for r in reminders:
            st.markdown(f"**{r['meeting_title']}** at {r['scheduled_time']} (Reminder: {r['reminder_time']})")
    else:
        st.info("No upcoming reminders.")
