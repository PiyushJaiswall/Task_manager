import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import io
import csv
import uuid
# Only import existing functions from supabase_client
from supabase_client import supabase

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
    .new-meeting-card {
        background: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #4CAF50;
        margin-bottom: 2rem;
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
        border: 1px solid #e9ecef;
    }
    /* Fix for table movement */
    .dataframe {
        position: relative;
    }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 8px;
    }
    .add-meeting-header {
        color: #2E7D32;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for caching
if 'stats_cache' not in st.session_state:
    st.session_state.stats_cache = None
if 'meetings_cache' not in st.session_state:
    st.session_state.meetings_cache = None
if 'cache_timestamp' not in st.session_state:
    st.session_state.cache_timestamp = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False

# Simplified functions that work directly with supabase
@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_meetings_cached():
    """Fetch meetings using direct supabase calls with caching"""
    try:
        response = supabase.table("meetings").select("*, transcripts(meeting_title, audio_url)").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching meetings: {str(e)}")
        return []

def create_new_meeting(title, summary, key_points, followup_points, next_meet_schedule=None, transcript_id=None):
    """Create a new meeting record"""
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
        # Clear cache after creation
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error creating meeting: {str(e)}")
        return False

def update_meeting_simple(meeting_id, title, summary, key_points, followup_points, next_meet_schedule=None):
    """Update meeting using direct supabase call"""
    try:
        update_data = {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "followup_points": followup_points
        }
        if next_meet_schedule:
            update_data["next_meet_schedule"] = next_meet_schedule

        response = supabase.table("meetings").update(update_data).eq("id", meeting_id).execute()
        # Clear cache after update
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating meeting: {str(e)}")
        return False

def fetch_transcript_simple(transcript_id):
    """Fetch transcript using direct supabase call"""
    try:
        response = supabase.table("transcripts").select("*").eq("id", transcript_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error fetching transcript: {str(e)}")
        return None

def get_stats_cached():
    """Get basic database stats with caching to prevent constant movement"""
    # Check if we have fresh cached data (within last 30 seconds)
    if (st.session_state.stats_cache is not None and 
        st.session_state.cache_timestamp is not None and
        (datetime.now() - st.session_state.cache_timestamp).seconds < 30):
        return st.session_state.stats_cache

    try:
        # Only fetch if we don't have recent data
        meetings_response = supabase.table("meetings").select("id", count="exact").execute()
        transcripts_response = supabase.table("transcripts").select("id", count="exact").execute()

        stats = {
            "meetings_count": meetings_response.count or 0,
            "transcripts_count": transcripts_response.count or 0,
            "meetings_size_mb": (meetings_response.count or 0) * 0.01,
            "transcripts_size_mb": (transcripts_response.count or 0) * 0.05,
            "total_size_mb": ((meetings_response.count or 0) * 0.01) + ((transcripts_response.count or 0) * 0.05)
        }

        # Cache the results
        st.session_state.stats_cache = stats
        st.session_state.cache_timestamp = datetime.now()

        return stats
    except Exception as e:
        st.error(f"Error getting stats: {str(e)}")
        # Return cached data if available, otherwise default
        if st.session_state.stats_cache:
            return st.session_state.stats_cache
        return {"meetings_count": 0, "transcripts_count": 0, "meetings_size_mb": 0, "transcripts_size_mb": 0, "total_size_mb": 0}

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

    # Add New Meeting Section
    col_header, col_toggle = st.columns([3, 1])
    with col_header:
        st.subheader("➕ Add New Meeting")
    with col_toggle:
        if st.button("📝 Add Manual Meeting" if not st.session_state.show_add_form else "❌ Cancel"):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.rerun()

    # Show add meeting form if toggled on
    if st.session_state.show_add_form:
        show_add_meeting_form()

    st.markdown("---")

    # Search and filter section for existing meetings
    st.subheader("📋 Existing Meetings")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_query = st.text_input("🔍 Search meetings by title or summary", placeholder="Type to search...")

    with col2:
        date_filter = st.date_input("📅 Filter by created date", value=None)

    with col3:
        if st.button("🔄 Refresh Data"):
            # Clear cache and refresh
            st.cache_data.clear()
            st.session_state.stats_cache = None
            st.session_state.meetings_cache = None
            st.rerun()

    # Fetch meetings from database (cached)
    meetings = fetch_meetings_cached()

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

def show_add_meeting_form():
    """Display the form for adding a new meeting manually"""
    with st.container():
        st.markdown('<div class="new-meeting-card">', unsafe_allow_html=True)
        st.markdown('<div class="add-meeting-header">Create New Meeting Record</div>', unsafe_allow_html=True)

        with st.form("add_new_meeting_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Meeting details
                new_title = st.text_input("Meeting Title *", placeholder="Enter meeting title...")

                new_summary = st.text_area(
                    "Meeting Summary *", 
                    placeholder="Summarize what was discussed in the meeting...",
                    height=120
                )

                new_key_points = st.text_area(
                    "Key Points (comma/semicolon separated)", 
                    placeholder="Key decision, Action item 1, Important discussion point...",
                    height=80
                )

                new_followup_points = st.text_area(
                    "Follow-up Points (comma/semicolon separated)", 
                    placeholder="Send report to team, Schedule follow-up meeting, Review proposal...",
                    height=80
                )

            with col2:
                # Meeting scheduling
                st.write("**Next Meeting Schedule (Optional)**")
                next_meeting_date = st.date_input(
                    "Date", 
                    value=None,
                    help="Select date for next meeting if applicable"
                )
                next_meeting_time = st.time_input(
                    "Time", 
                    value=datetime.now().time(),
                    help="Select time for next meeting"
                )

                st.write("**Meeting Type**")
                meeting_type = st.selectbox(
                    "Type",
                    ["Manual Entry", "Follow-up Meeting", "Regular Meeting", "Ad-hoc Meeting", "Review Meeting"],
                    help="Select the type of meeting"
                )

                st.write("**Priority**")
                priority = st.selectbox(
                    "Priority Level",
                    ["Medium", "High", "Low", "Critical"],
                    help="Set priority level for this meeting"
                )

            # Submit button
            col_submit, col_clear = st.columns([2, 1])
            with col_submit:
                submit_clicked = st.form_submit_button("✅ Create Meeting", use_container_width=True, type="primary")
            with col_clear:
                if st.form_submit_button("🔄 Clear Form", use_container_width=True):
                    st.rerun()

            # Handle form submission
            if submit_clicked:
                if new_title.strip() and new_summary.strip():
                    create_manual_meeting(
                        new_title.strip(),
                        new_summary.strip(), 
                        new_key_points,
                        new_followup_points,
                        next_meeting_date,
                        next_meeting_time,
                        meeting_type,
                        priority
                    )
                else:
                    st.error("Please fill in both Title and Summary fields (marked with *)")

        st.markdown('</div>', unsafe_allow_html=True)

def create_manual_meeting(title, summary, key_points, followup_points, next_date, next_time, meeting_type, priority):
    """Process and create a new manual meeting"""
    try:
        # Process key points and followup points
        key_points_list = [point.strip() for point in key_points.replace(';', ',').split(',') if point.strip()]
        followup_points_list = [point.strip() for point in followup_points.replace(';', ',').split(',') if point.strip()]

        # Add metadata to key points
        if meeting_type != "Manual Entry":
            key_points_list.append(f"Meeting Type: {meeting_type}")
        if priority != "Medium":
            key_points_list.append(f"Priority: {priority}")

        # Combine date and time for next meeting
        next_meeting = None
        if next_date and next_time:
            next_meeting = datetime.combine(next_date, next_time).isoformat()
        elif next_date:
            next_meeting = datetime.combine(next_date, datetime.min.time()).isoformat()

        # Create meeting in database
        success = create_new_meeting(
            title,
            summary,
            key_points_list,
            followup_points_list,
            next_meeting
        )

        if success:
            st.success(f"✅ Meeting '{title}' created successfully!")
            st.session_state.show_add_form = False
            st.balloons()  # Fun celebration effect
            st.rerun()
        else:
            st.error("❌ Failed to create meeting")

    except Exception as e:
        st.error(f"Error creating meeting: {str(e)}")

def display_meeting_card(meeting):
    with st.container():
        st.markdown('<div class="meeting-card">', unsafe_allow_html=True)

        # Meeting title with indicator for manual vs transcript-based
        title = meeting.get("title", "Untitled Meeting")
        if not meeting.get('transcript_id'):
            title_display = f"📝 {title}"  # Manual meeting indicator
        else:
            title_display = f"🎤 {title}"  # Transcript-based meeting indicator

        st.markdown(f'<div class="meeting-title">{title_display}</div>', unsafe_allow_html=True)

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

        # Show meeting source
        source_type = "Manual Entry" if not meeting.get('transcript_id') else "From Transcript"
        st.markdown(f'<div class="meeting-meta">Source: {source_type} | Created: {created_str} | Updated: {updated_str}</div>', 
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
                save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")

                # Only show transcript download for meetings that have transcripts
                if meeting.get('transcript_id'):
                    transcript_clicked = st.form_submit_button("📄 Download Transcript", use_container_width=True)
                else:
                    st.info("📝 Manual entry - no transcript available")
                    transcript_clicked = False

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

            if transcript_clicked and meeting.get('transcript_id'):
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
        success = update_meeting_simple(
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

    transcript = fetch_transcript_simple(transcript_id)
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

def space_management_tab():
    st.header("Database Space Management")

    # Database stats section
    st.subheader("📊 Database Statistics")

    # Get stats with caching to prevent constant movement
    stats = get_stats_cached()

    # Use metrics instead of custom HTML to prevent movement
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Meetings",
            value=stats.get('meetings_count', 0),
            delta=None
        )

    with col2:
        st.metric(
            label="Total Transcripts", 
            value=stats.get('transcripts_count', 0),
            delta=None
        )

    with col3:
        st.metric(
            label="Storage Used (MB)",
            value=f"{stats.get('total_size_mb', 0):.2f}",
            delta=None
        )

    # Detailed table sizes - FIXED to prevent movement
    st.subheader("📋 Table Details")

    # Create a stable dataframe that doesn't constantly refresh
    table_data = pd.DataFrame({
        'Table': ['meetings', 'transcripts'],
        'Record Count': [stats.get('meetings_count', 0), stats.get('transcripts_count', 0)],
        'Size (MB)': [f"{stats.get('meetings_size_mb', 0):.3f}", f"{stats.get('transcripts_size_mb', 0):.3f}"]
    })

    # Display with fixed styling
    st.dataframe(
        table_data, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Table": st.column_config.TextColumn("Table", width="medium"),
            "Record Count": st.column_config.NumberColumn("Record Count", width="medium"),
            "Size (MB)": st.column_config.TextColumn("Size (MB)", width="medium")
        }
    )

    # Show cache info
    if st.session_state.cache_timestamp:
        cache_age = (datetime.now() - st.session_state.cache_timestamp).seconds
        st.caption(f"📊 Data refreshed {cache_age} seconds ago")

    st.markdown("---")

    # Manual refresh button for stats
    col_refresh, col_space = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh Stats", help="Manually refresh database statistics"):
            st.session_state.stats_cache = None
            st.session_state.cache_timestamp = None
            st.rerun()

    # Basic cleanup and export (simplified)
    st.subheader("🧹 Database Management")
    st.info("💡 To enable advanced cleanup and export features, please update your supabase_client.py file with the complete version.")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Delete Old Records**")
        cutoff_date = st.date_input("Delete records older than:", value=date.today() - timedelta(days=30))
        if st.button("🗑️ Delete Old Records (Coming Soon)", disabled=True):
            st.info("This feature requires the complete supabase_client.py update")

    with col2:
        st.write("**Export Data**")
        start_date = st.date_input("Export from:", value=date.today() - timedelta(days=30))
        end_date = st.date_input("Export to:", value=date.today())
        if st.button("📤 Export to CSV (Coming Soon)", disabled=True):
            st.info("This feature requires the complete supabase_client.py update")

if __name__ == "__main__":
    main()
