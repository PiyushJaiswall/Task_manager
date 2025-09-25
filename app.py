import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import io
import csv
from supabase_client import (
    supabase,
    fetch_meetings,
    fetch_meeting_by_id,
    update_meeting,
    fetch_transcript_by_id,
    get_database_stats,
    delete_old_records,
    export_meetings_csv
)

# Configure Streamlit page
st.set_page_config(
    page_title="Meeting Transcript Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .meeting-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .meeting-title {
        color: #1f1f1f;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .meeting-meta {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
    .stats-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📝 Meeting Transcript Manager")

    # Create tabs
    tab1, tab2 = st.tabs(["📋 Meet Details", "🗄️ Space Management"])

    with tab1:
        meet_details_tab()

    with tab2:
        space_management_tab()

def meet_details_tab():
    st.header("Meeting Details Management")

    # Search and filter section
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_query = st.text_input("🔍 Search meetings by title or summary", placeholder="Type to search...")

    with col2:
        date_filter = st.date_input("📅 Filter by created date", value=None)

    with col3:
        if st.button("🔄 Refresh Data"):
            st.rerun()

    # Fetch meetings from database
    try:
        meetings = fetch_meetings()

        if not meetings:
            st.info("No meetings found in the database.")
            return

        # Apply filters
        filtered_meetings = meetings.copy()

        # Search filter
        if search_query:
            filtered_meetings = [
                meeting for meeting in filtered_meetings
                if search_query.lower() in (meeting.get('title', '') or '').lower() or
                   search_query.lower() in (meeting.get('summary', '') or '').lower()
            ]

        # Date filter
        if date_filter:
            filtered_meetings = [
                meeting for meeting in filtered_meetings
                if meeting.get('created_at') and 
                   datetime.fromisoformat(meeting['created_at'].replace('Z', '+00:00')).date() == date_filter
            ]

        st.write(f"Found {len(filtered_meetings)} meeting(s)")

        # Display meetings as cards
        for meeting in filtered_meetings:
            display_meeting_card(meeting)

    except Exception as e:
        st.error(f"Error loading meetings: {str(e)}")

def display_meeting_card(meeting):
    with st.container():
        st.markdown('<div class="meeting-card">', unsafe_allow_html=True)

        # Meeting title
        st.markdown(f'<div class="meeting-title">{meeting.get("title", "Untitled Meeting")}</div>', 
                   unsafe_allow_html=True)

        # Meeting metadata
        created_at = meeting.get('created_at', '')
        updated_at = meeting.get('updated_at', '')
        if created_at:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_str = created_dt.strftime("%Y-%m-%d %H:%M")
        else:
            created_str = "Unknown"

        if updated_at:
            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            updated_str = updated_dt.strftime("%Y-%m-%d %H:%M")
        else:
            updated_str = "Unknown"

        st.markdown(f'<div class="meeting-meta">Created: {created_str} | Updated: {updated_str}</div>', 
                   unsafe_allow_html=True)

        # Create form for editing
        with st.form(key=f"meeting_form_{meeting['id']}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Editable fields
                new_title = st.text_input("Title", value=meeting.get('title', ''), key=f"title_{meeting['id']}")

                new_summary = st.text_area("Summary", value=meeting.get('summary', ''), 
                                         height=100, key=f"summary_{meeting['id']}")

                # Key points - convert array to comma-separated string
                key_points_str = ', '.join(meeting.get('key_points', []) or [])
                new_key_points = st.text_area("Key Points (comma/semicolon separated)", 
                                            value=key_points_str, key=f"key_points_{meeting['id']}")

                # Follow-up points
                followup_points_str = ', '.join(meeting.get('followup_points', []) or [])
                new_followup_points = st.text_area("Follow-up Points (comma/semicolon separated)", 
                                                 value=followup_points_str, key=f"followup_{meeting['id']}")

            with col2:
                # Next meeting schedule
                next_meet = meeting.get('next_meet_schedule')
                if next_meet:
                    next_meet_date = datetime.fromisoformat(next_meet.replace('Z', '+00:00')).date()
                    next_meet_time = datetime.fromisoformat(next_meet.replace('Z', '+00:00')).time()
                else:
                    next_meet_date = None
                    next_meet_time = None

                new_next_date = st.date_input("Next Meeting Date", value=next_meet_date, 
                                            key=f"next_date_{meeting['id']}")
                new_next_time = st.time_input("Next Meeting Time", value=next_meet_time, 
                                            key=f"next_time_{meeting['id']}")

                # Action buttons
                col_save, col_transcript = st.columns(2)

                with col_save:
                    save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)

                with col_transcript:
                    transcript_clicked = st.form_submit_button("📄 Download Transcript", use_container_width=True)

            # Handle form submissions
            if save_clicked:
                save_meeting_changes(
                    meeting['id'],
                    new_title,
                    new_summary,
                    new_key_points,
                    new_followup_points,
                    new_next_date,
                    new_next_time
                )

            if transcript_clicked:
                download_transcript(meeting.get('transcript_id'))

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

def save_meeting_changes(meeting_id, title, summary, key_points, followup_points, next_date, next_time):
    try:
        # Process key points and followup points
        key_points_list = [point.strip() for point in key_points.replace(';', ',').split(',') if point.strip()]
        followup_points_list = [point.strip() for point in followup_points.replace(';', ',').split(',') if point.strip()]

        # Combine date and time for next meeting
        next_meeting = None
        if next_date and next_time:
            next_meeting = datetime.combine(next_date, next_time).isoformat()
        elif next_date:
            next_meeting = datetime.combine(next_date, datetime.min.time()).isoformat()

        # Update meeting in database
        success = update_meeting(
            meeting_id,
            title,
            summary,
            key_points_list,
            followup_points_list,
            next_meeting
        )

        if success:
            st.success("Meeting updated successfully!")
            st.rerun()
        else:
            st.error("Failed to update meeting")

    except Exception as e:
        st.error(f"Error updating meeting: {str(e)}")

def download_transcript(transcript_id):
    if not transcript_id:
        st.warning("No transcript linked to this meeting")
        return

    try:
        transcript = fetch_transcript_by_id(transcript_id)
        if transcript:
            # Create download link
            transcript_text = transcript.get('transcript_text', '')
            meeting_title = transcript.get('meeting_title', 'meeting')

            if transcript_text:
                st.download_button(
                    label="📥 Download Transcript",
                    data=transcript_text,
                    file_name=f"{meeting_title}_transcript.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Transcript text is empty")
        else:
            st.error("Transcript not found")

    except Exception as e:
        st.error(f"Error downloading transcript: {str(e)}")

def space_management_tab():
    st.header("Database Space Management")

    # Database stats section
    st.subheader("📊 Database Statistics")

    try:
        stats = get_database_stats()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="stats-card">
                <h3>Total Meetings</h3>
                <h2 style="color: #1f77b4;">{}</h2>
            </div>
            """.format(stats.get('meetings_count', 0)), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="stats-card">
                <h3>Total Transcripts</h3>
                <h2 style="color: #ff7f0e;">{}</h2>
            </div>
            """.format(stats.get('transcripts_count', 0)), unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="stats-card">
                <h3>Storage Used</h3>
                <h2 style="color: #2ca02c;">{:.2f} MB</h2>
            </div>
            """.format(stats.get('total_size_mb', 0)), unsafe_allow_html=True)

        # Detailed table sizes
        st.subheader("📋 Table Details")
        table_data = {
            'Table': ['meetings', 'transcripts'],
            'Record Count': [stats.get('meetings_count', 0), stats.get('transcripts_count', 0)],
            'Size (MB)': [stats.get('meetings_size_mb', 0), stats.get('transcripts_size_mb', 0)]
        }
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    except Exception as e:
        st.error(f"Error loading database stats: {str(e)}")

    st.markdown("---")

    # Cleanup section
    st.subheader("🧹 Database Cleanup")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Delete Old Records**")
        cutoff_date = st.date_input("Delete records older than:", value=date.today() - timedelta(days=30))

        if st.button("🗑️ Delete Old Records", type="secondary"):
            if st.session_state.get('confirm_delete'):
                try:
                    deleted_count = delete_old_records(cutoff_date.isoformat())
                    st.success(f"Deleted {deleted_count} old records")
                    st.session_state.confirm_delete = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting records: {str(e)}")
            else:
                st.warning("⚠️ This will permanently delete old records. Click again to confirm.")
                st.session_state.confirm_delete = True

    with col2:
        st.write("**Export Data**")
        start_date = st.date_input("Export from:", value=date.today() - timedelta(days=30))
        end_date = st.date_input("Export to:", value=date.today())

        if st.button("📤 Export to CSV"):
            try:
                csv_data = export_meetings_csv(start_date.isoformat(), end_date.isoformat())

                if csv_data:
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"meetings_export_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No data found for the selected date range")

            except Exception as e:
                st.error(f"Error exporting data: {str(e)}")

if __name__ == "__main__":
    main()
