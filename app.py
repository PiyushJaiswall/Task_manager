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

# Enhanced CSS for better card visibility and contrast
st.markdown("""
<style>
    /* Hide Streamlit's default containers that create unwanted rectangles */
    .element-container:has(> .stMarkdown > div > div[data-testid="column"]) {
        display: none;
    }

    /* Main app background - darker for better contrast */
    .main .block-container {
        background-color: #1a202c;
        padding-top: 2rem;
    }

    /* Better contrast meeting cards */
    .meeting-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        color: #1a202c;
        padding: 2rem;
        border-radius: 16px;
        border: 2px solid #e2e8f0;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        position: relative;
        transition: all 0.3s ease;
    }

    .meeting-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 35px rgba(0, 0, 0, 0.2);
        border-color: #4299e1;
    }

    /* Alternate card colors for better distinction */
    .meeting-card:nth-child(even) {
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
    }

    /* New meeting form card - distinct blue theme */
    .new-meeting-card {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        border: 2px solid #2b6cb0;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(66, 153, 225, 0.3);
    }

    /* Meeting title - high contrast */
    .meeting-title {
        color: #1a202c !important;
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: none;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }

    /* Meeting metadata */
    .meeting-meta {
        color: #4a5568 !important;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
        font-style: italic;
        background: #f7fafc;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #4299e1;
    }

    /* Mode indicators with better colors */
    .edit-mode-indicator {
        position: absolute;
        top: 15px;
        right: 15px;
        background: #48bb78;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .view-mode-indicator {
        position: absolute;
        top: 15px;
        right: 15px;
        background: #4299e1;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    /* Read-only field styling - light theme compatible */
    .readonly-field {
        background: #f7fafc !important;
        color: #2d3748 !important;
        border: 2px solid #e2e8f0 !important;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 1rem;
        font-weight: 500;
    }

    .readonly-textarea {
        background: #f7fafc !important;
        color: #2d3748 !important;
        border: 2px solid #e2e8f0 !important;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        min-height: 100px;
        white-space: pre-wrap;
        font-family: inherit;
        line-height: 1.5;
        font-size: 0.95rem;
    }

    /* Button styling improvements */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 2px solid transparent;
        padding: 0.5rem 1rem;
    }

    /* Section headers with better contrast */
    .section-header {
        color: #e2e8f0 !important;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #4a5568 0%, #2d3748 100%);
        border-radius: 12px;
        border-left: 5px solid #4299e1;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    /* Add meeting header */
    .add-meeting-header {
        color: white !important;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    /* Remove unwanted containers and rectangles */
    .stContainer > div:empty {
        display: none;
    }

    /* Fix empty divs that create rectangles */
    div[data-testid="column"]:empty {
        display: none;
    }

    /* Remove any empty elements that might create unwanted blocks */
    .element-container:empty,
    .stMarkdown:empty,
    .stColumns:empty {
        display: none;
    }

    /* Stats cards for space management */
    .stats-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        color: #1a202c;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Input field improvements for better visibility */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border-color: #cbd5e0 !important;
        border-width: 2px !important;
    }

    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border-color: #cbd5e0 !important;
        border-width: 2px !important;
    }

    .stSelectbox > div > div > div {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border-color: #cbd5e0 !important;
    }

    /* Card container wrapper */
    .card-wrapper {
        margin-bottom: 0;
        padding: 0;
    }

    /* Hide any remaining empty containers */
    .streamlit-container:empty,
    .row-widget:empty,
    .widget:empty {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for caching and edit modes
if 'stats_cache' not in st.session_state:
    st.session_state.stats_cache = None
if 'meetings_cache' not in st.session_state:
    st.session_state.meetings_cache = None
if 'cache_timestamp' not in st.session_state:
    st.session_state.cache_timestamp = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_modes' not in st.session_state:
    st.session_state.edit_modes = {}  # Track edit mode for each meeting

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
        st.markdown('<div class="section-header">➕ Add New Meeting</div>', unsafe_allow_html=True)
    with col_toggle:
        if st.button("📝 Add Manual Meeting" if not st.session_state.show_add_form else "❌ Cancel"):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.rerun()

    # Show add meeting form if toggled on
    if st.session_state.show_add_form:
        show_add_meeting_form()

    st.markdown("---")

    # Search and filter section for existing meetings
    st.markdown('<div class="section-header">📋 Existing Meetings</div>', unsafe_allow_html=True)
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

    # Display meetings as cards - removed any potential empty containers
    for i, meeting in enumerate(filtered_meetings):
        display_meeting_card(meeting, i)

def show_add_meeting_form():
    """Display the form for adding a new meeting manually"""
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

def display_meeting_card(meeting, index):
    meeting_id = meeting['id']
    is_edit_mode = st.session_state.edit_modes.get(meeting_id, False)

    # Use a unique key wrapper to prevent empty container issues
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="meeting-card">', unsafe_allow_html=True)

    # Edit mode indicator
    if is_edit_mode:
        st.markdown('<div class="edit-mode-indicator">✏️ EDITING</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="view-mode-indicator">👁️ VIEW</div>', unsafe_allow_html=True)

    # Meeting title with better contrast
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
    st.markdown(f'<div class="meeting-meta">📋 Source: {source_type} | 📅 Created: {created_str} | 🔄 Updated: {updated_str}</div>', 
               unsafe_allow_html=True)

    # Edit/View toggle buttons at top of card
    col_edit, col_transcript, col_spacer = st.columns([1, 1, 2])

    with col_edit:
        if is_edit_mode:
            if st.button("❌ Cancel", key=f"cancel_{meeting_id}", help="Cancel editing"):
                st.session_state.edit_modes[meeting_id] = False
                st.rerun()
        else:
            if st.button("✏️ Edit", key=f"edit_{meeting_id}", help="Enable editing"):
                st.session_state.edit_modes[meeting_id] = True
                st.rerun()

    with col_transcript:
        # Only show transcript download for meetings that have transcripts
        if meeting.get('transcript_id'):
            if st.button("📄 Transcript", key=f"transcript_{meeting_id}", help="Download transcript"):
                download_transcript(meeting.get('transcript_id'))
        else:
            st.markdown('<div style="text-align: center; color: #4a5568; font-size: 0.9rem; padding: 8px; background: #f7fafc; border-radius: 6px;">📝 Manual Entry</div>', 
                       unsafe_allow_html=True)

    # Main content area
    if is_edit_mode:
        # Edit mode - show editable form
        with st.form(key=f"meeting_edit_form_{meeting_id}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Editable fields
                new_title = st.text_input("Title", value=meeting.get('title', ''), key=f"edit_title_{meeting_id}")

                new_summary = st.text_area("Summary", value=meeting.get('summary', ''), 
                                         height=100, key=f"edit_summary_{meeting_id}")

                # Key points - convert array to comma-separated string
                key_points_str = ', '.join(meeting.get('key_points', []) or [])
                new_key_points = st.text_area("Key Points (comma/semicolon separated)", 
                                            value=key_points_str, key=f"edit_key_points_{meeting_id}")

                # Follow-up points
                followup_points_str = ', '.join(meeting.get('followup_points', []) or [])
                new_followup_points = st.text_area("Follow-up Points (comma/semicolon separated)", 
                                                 value=followup_points_str, key=f"edit_followup_{meeting_id}")

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
                                            key=f"edit_next_date_{meeting_id}")
                new_next_time = st.time_input("Next Meeting Time", value=next_meet_time, 
                                            key=f"edit_next_time_{meeting_id}")

            # Save button
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")

            # Handle form submission
            if save_clicked:
                success = save_meeting_changes(
                    meeting_id,
                    new_title,
                    new_summary,
                    new_key_points,
                    new_followup_points,
                    new_next_date,
                    new_next_time
                )
                if success:
                    st.session_state.edit_modes[meeting_id] = False
                    st.rerun()

    else:
        # View mode - show read-only content
        col1, col2 = st.columns([2, 1])

        with col1:
            # Read-only title
            st.write("**Title:**")
            st.markdown(f'<div class="readonly-field">{meeting.get("title", "Untitled")}</div>', 
                       unsafe_allow_html=True)

            # Read-only summary
            st.write("**Summary:**")
            summary_text = meeting.get('summary', 'No summary available')
            st.markdown(f'<div class="readonly-textarea">{summary_text}</div>', 
                       unsafe_allow_html=True)

            # Read-only key points
            st.write("**Key Points:**")
            key_points_text = ', '.join(meeting.get('key_points', []) or ['No key points'])
            st.markdown(f'<div class="readonly-textarea">{key_points_text}</div>', 
                       unsafe_allow_html=True)

            # Read-only follow-up points
            st.write("**Follow-up Points:**")
            followup_text = ', '.join(meeting.get('followup_points', []) or ['No follow-up points'])
            st.markdown(f'<div class="readonly-textarea">{followup_text}</div>', 
                       unsafe_allow_html=True)

        with col2:
            # Next meeting info
            st.write("**Next Meeting:**")
            next_meet = meeting.get('next_meet_schedule')
            if next_meet:
                next_meet_dt = datetime.fromisoformat(next_meet.replace('Z', '+00:00'))
                next_meet_str = next_meet_dt.strftime("%Y-%m-%d at %H:%M")
                st.markdown(f'<div class="readonly-field">📅 {next_meet_str}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown('<div class="readonly-field">⏸️ Not scheduled</div>', 
                           unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
            return True
        else:
            st.error("Failed to update meeting")
            return False

    except Exception as e:
        st.error(f"Error updating meeting: {str(e)}")
        return False

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
