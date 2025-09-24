import streamlit as st
from datetime import datetime
from supabase_client import fetch_transcripts, save_schedule, fetch_upcoming_reminders, delete_transcript, delete_schedule, sign_in

st.set_page_config(page_title="BizExpress Dashboard", layout="wide")
st.title("BizExpress Meeting Dashboard")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    auth_tab = st.tabs(["Login", "Sign Up"])
    
    # ---------------------
    # LOGIN FORM
    # ---------------------
    with auth_tab[0]:
        with st.form("login_form"):
            user_email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            login_submitted = st.form_submit_button("Login")

        if login_submitted:
            if not user_email or not password:
                st.error("Please enter both email and password.")
            else:
                if sign_in(user_email, password):
                    st.success(f"Logged in as {user_email}")
                    st.session_state.logged_in = True
                    st.session_state.user_email = user_email
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password")

    # ---------------------
    # SIGNUP FORM
    # ---------------------
    with auth_tab[1]:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            signup_submitted = st.form_submit_button("Sign Up")

        if signup_submitted:
            if not new_email or not new_password:
                st.error("Please enter both email and password.")
            else:
                if sign_up(new_email, new_password):
                    st.success("Signup successful! You can now login.")
                else:
                    st.error("Signup failed. Email might already be in use.")
else:
    user_email = st.session_state.user_email


    # ---------------------
    # Tabs for dashboard
    # ---------------------
    tabs = st.tabs(["Meeting Summaries", "Schedule Meetings", "Upcoming Reminders", "Storage & Cleanup"])

    # --- TAB 1: Meeting Summaries ---
    with tabs[0]:
        st.header("Meeting Summaries")
        transcripts = fetch_transcripts(user_email)
        if transcripts:
            for t in transcripts:
                with st.expander(f"{t['meeting_name']} ({t['start_time']})"):
                    st.write(f"Start: {t['start_time']}, End: {t.get('end_time', 'N/A')}")
                    st.write(t.get("transcript_text", ""))
                    if st.button(f"Delete Transcript {t['id']}", key=f"del_{t['id']}"):
                        delete_transcript(t['id'])
                        st.success("Transcript deleted!")
                        st.experimental_rerun()
        else:
            st.info("No transcripts available.")

    # --- TAB 2: Schedule Meetings ---
    with tabs[1]:
        st.header("Auto-Schedule Next Meeting")
        last_summary = transcripts[0]["transcript_text"] if transcripts else ""
        suggested_title = transcripts[0]["meeting_name"] + " - Follow up" if transcripts else "Next Meeting"
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
                st.experimental_rerun()

        st.header("Manual Schedule Creation")
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
                st.experimental_rerun()

    # --- TAB 3: Upcoming Reminders ---
    with tabs[2]:
        st.header("Upcoming Reminders")
        reminders = fetch_upcoming_reminders(user_email)
        if reminders:
            for r in reminders:
                with st.expander(f"{r['meeting_title']} at {r['scheduled_time']}"):
                    st.write(f"Notes: {r.get('notes', '')}")
                    if st.button(f"Delete Reminder {r['id']}", key=f"del_rem_{r['id']}"):
                        delete_schedule(r['id'])
                        st.success("Reminder deleted!")
                        st.experimental_rerun()
        else:
            st.info("No upcoming reminders.")

    # --- TAB 4: Storage & Cleanup ---
    with tabs[3]:
        st.header("Manage Stored Data")
        st.subheader("Transcripts")
        if transcripts:
            for t in transcripts:
                st.write(f"{t['meeting_name']} ({t['start_time']})")
                if st.button(f"Delete Transcript {t['id']}", key=f"storage_del_{t['id']}"):
                    delete_transcript(t['id'])
                    st.success("Transcript deleted!")
                    st.experimental_rerun()
        else:
            st.info("No transcripts stored.")

        st.subheader("Scheduled Meetings / Reminders")
        if reminders:
            for r in reminders:
                st.write(f"{r['meeting_title']} at {r['scheduled_time']}")
                if st.button(f"Delete Reminder {r['id']}", key=f"storage_del_rem_{r['id']}"):
                    delete_schedule(r['id'])
                    st.success("Reminder deleted!")
                    st.experimental_rerun()
        else:
            st.info("No scheduled reminders.")

