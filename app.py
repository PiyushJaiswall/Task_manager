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

# Custom CSS for your exact layout requirements
st.markdown("""
<style>
    /* Dark theme background */
    .main .block-container {
        background-color: #1a202c;
        color: #e2e8f0;
        padding: 1rem 2rem;
    }

    /* Top controls layout */
    .top-controls-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding: 1rem 2rem;
        background: #2d3748;
        border-radius: 12px;
        border: 1px solid #4a5568;
    }

    .right-controls {
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    /* Meeting preview cards - 1/5th size, landscape phone style */
    .meeting-preview-card {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        color: #1a202c;
        padding: 1rem;
        margin: 0.5rem;
        border-radius: 12px;
        border: 2px solid #cbd5e0;
        width: calc(20% - 1rem);
        height: 140px;
        display: inline-block;
        cursor: pointer;
        transition: all 0.3s ease;
        vertical-align: top;
        position: relative;
        overflow: hidden;
        box-sizing: border-box;
    }

    .meeting-preview-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(66, 153, 225, 0.3);
        border-color: #4299e1;
    }

    /* Meeting preview content */
    .preview-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.5rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .preview-source {
        font-size: 0.75rem;
        color: #4a5568;
        margin-bottom: 0.5rem;
    }

    .preview-dates {
        font-size: 0.7rem;
        color: #718096;
        line-height: 1.3;
        position: absolute;
        bottom: 0.5rem;
        left: 1rem;
        right: 1rem;
    }

    /* Meeting cards container */
    .meetings-container {
        min-height: 500px;
        padding: 2rem;
        background: #2d3748;
        border-radius: 12px;
        border: 1px solid #4a5568;
        text-align: left;
    }

    /* Add meeting form */
    .add-meeting-form {
        background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
        color: #1a202c;
        padding: 2rem;
        margin: 2rem 0;
        border-radius: 16px;
        border: 2px solid #38b2ac;
        box-shadow: 0 8px 25px rgba(56, 178, 172, 0.2);
    }

    .form-header {
        background: linear-gradient(90deg, #38b2ac 0%, #319795 100%);
        color: white;
        padding: 1rem 1.5rem;
        margin: -2rem -2rem 2rem -2rem;
        border-radius: 14px 14px 0 0;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
    }

    /* Detail modal styling */
    .detail-section {
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        background: #f8f9fa;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }

    .detail-section h3 {
        color: #2d3748;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #cbd5e0;
    }

    /* Form styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border: 2px solid #cbd5e0 !important;
        border-radius: 8px !important;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    /* Hide empty containers */
    .element-container:empty {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'stats_cache' not in st.session_state:
    st.session_state.stats_cache = None
if 'meetings_cache' not in st.session_state:
    st.session_state.meetings_cache = None
if 'cache_timestamp' not in st.session_state:
    st.session_state.cache_timestamp = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'selected_meeting' not in st.session_state:
    st.session_state.selected_meeting = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Database functions
@st.cache_data(ttl=30)
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
    """Get basic database stats with caching"""
    if (st.session_state.stats_cache is not None and 
        st.session_state.cache_timestamp is not None and
        (datetime.now() - st.session_state.cache_timestamp).seconds < 30):
        return st.session_state.stats_cache

    try:
        meetings_response = supabase.table("meetings").select("id", count="exact").execute()
        transcripts_response = supabase.table("transcripts").select("id", count="exact").execute()

        stats = {
            "meetings_count": meetings_response.count or 0,
            "transcripts_count": transcripts_response.count or 0,
            "meetings_size_mb": (meetings_response.count or 0) * 0.01,
            "transcripts_size_mb": (transcripts_response.count or 0) * 0.05,
            "total_size_mb": ((meetings_response.count or 0) * 0.01) + ((transcripts_response.count or 0) * 0.05)
        }

        st.session_state.stats_cache = stats
        st.session_state.cache_timestamp = datetime.now()
        return stats
    except Exception as e:
        st.error(f"Error getting stats: {str(e)}")
        if st.session_state.stats_cache:
            return st.session_state.stats_cache
        return {"meetings_count": 0, "transcripts_count": 0, "meetings_size_mb": 0, "transcripts_size_mb": 0, "total_size_mb": 0}

def main():
    st.title("📝 Meeting Transcript Manager")

    # Create tabs - keeping both as requested
    tab1, tab2 = st.tabs(["📋 Meet Details", "🗄️ Space Management"])

    with tab1:
        meet_details_tab()

    with tab2:
        space_management_tab()  # Keep unchanged

def meet_details_tab():
    # Exact top layout as requested
    col_left, col_right = st.columns([1, 3])

    with col_left:
        # Add Manual Meeting button (top-left)
        if st.button("➕ Add Manual Meeting", type="primary", use_container_width=True):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.rerun()

    with col_right:
        # Search + Filter + Refresh (top-right)
        col_search, col_filter, col_refresh = st.columns([2, 1, 1])

        with col_search:
            search_query = st.text_input("Search meetings by title or summary", placeholder="Type to search...", key="search_input")

        with col_filter:
            date_filter = st.date_input("Filter by created date", value=None, key="date_filter")

        with col_refresh:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.session_state.stats_cache = None
                st.rerun()

    # Add Meeting Form (when toggled)
    if st.session_state.show_add_form:
        show_add_meeting_form()

    # Main meetings display area
    st.markdown('<div class="meetings-container">', unsafe_allow_html=True)

    # Fetch and filter meetings
    meetings = fetch_meetings_cached()

    if not meetings:
        st.info("📭 No meetings found in the database.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Apply filters
    filtered_meetings = meetings.copy()

    if search_query:
        filtered_meetings = [
            meeting for meeting in filtered_meetings
            if search_query.lower() in (meeting.get('title', '') or '').lower() or
               search_query.lower() in (meeting.get('summary', '') or '').lower()
        ]

    if date_filter:
        filtered_meetings = [
            meeting for meeting in filtered_meetings
            if meeting.get('created_at') and 
               datetime.fromisoformat(meeting['created_at'].replace('Z', '+00:00')).date() == date_filter
        ]

    # Display meeting preview cards (1/5th size, landscape phone style)
    st.write(f"Found {len(filtered_meetings)} meeting(s)")
    st.write("")  # Add some space

    # Create grid of preview cards
    for i, meeting in enumerate(filtered_meetings):
        if i % 5 == 0:  # New row every 5 cards
            cols = st.columns(5)

        with cols[i % 5]:
            display_meeting_preview(meeting)

    st.markdown('</div>', unsafe_allow_html=True)

    # Show selected meeting detail modal
    if st.session_state.selected_meeting:
        show_meeting_detail_modal()

def display_meeting_preview(meeting):
    """Display small preview card (1/5th size, landscape phone style)"""
    # Format dates
    created_at = meeting.get('created_at', '')
    updated_at = meeting.get('updated_at', '')

    if created_at:
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        created_str = created_dt.strftime("%m-%d %H:%M")
    else:
        created_str = "Unknown"

    if updated_at:
        updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        updated_str = updated_dt.strftime("%m-%d %H:%M")
    else:
        updated_str = "Unknown"

    # Source type and icon
    source_icon = "📝" if not meeting.get('transcript_id') else "🎤"
    source_type = "Manual" if not meeting.get('transcript_id') else "Transcript"

    # Create title (truncated)
    title = meeting.get('title', 'Untitled Meeting')
    display_title = title[:25] + ('...' if len(title) > 25 else '')

    # Create preview card as button with custom styling
    card_content = f"""
**{source_icon} {display_title}**
📋 {source_type}
📅 Created: {created_str}
🔄 Updated: {updated_str}
"""

    # Use expander-style button for card appearance
    if st.button(card_content, key=f"card_{meeting['id']}", help="Click to view details", use_container_width=True):
        st.session_state.selected_meeting = meeting
        st.session_state.edit_mode = False
        st.rerun()

def show_meeting_detail_modal():
    """Show detailed meeting view"""
    meeting = st.session_state.selected_meeting

    st.markdown("---")
    st.markdown("## 📋 Meeting Details")

    # Modal header
    col_title, col_edit, col_close = st.columns([2, 1, 1])

    with col_title:
        source_icon = "📝" if not meeting.get('transcript_id') else "🎤"
        st.markdown(f"### {source_icon} {meeting.get('title', 'Untitled Meeting')}")

    with col_edit:
        if st.button("✏️ Edit" if not st.session_state.edit_mode else "👁️ View", key="edit_toggle", use_container_width=True):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()

    with col_close:
        if st.button("❌ Close", key="close_modal", use_container_width=True):
            st.session_state.selected_meeting = None
            st.session_state.edit_mode = False
            st.rerun()

    st.markdown("---")

    if st.session_state.edit_mode:
        show_edit_form(meeting)
    else:
        show_meeting_details(meeting)

def show_meeting_details(meeting):
    """Show meeting details in read-only mode"""
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

    source_type = "Manual Entry" if not meeting.get('transcript_id') else "From Transcript"

    # Display metadata
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        st.info(f"📋 **Source:** {source_type}")
        st.info(f"📅 **Created:** {created_str}")
    with col_meta2:
        st.info(f"🔄 **Updated:** {updated_str}")
        if meeting.get('transcript_id'):
            if st.button("📄 Download Transcript", key="download_transcript"):
                download_transcript(meeting.get('transcript_id'))

    st.markdown("---")

    # Content sections
    col1, col2 = st.columns([2, 1])

    with col1:
        # Title
        st.markdown("### 📝 Title")
        st.markdown(f"**{meeting.get('title', 'Untitled Meeting')}**")
        st.markdown("")

        # Summary
        st.markdown("### 📄 Summary")
        summary = meeting.get('summary', 'No summary available')
        st.markdown(summary)
        st.markdown("")

        # Key Points
        st.markdown("### 🎯 Key Points")
        key_points = meeting.get('key_points', [])
        if key_points:
            for point in key_points:
                st.markdown(f"• {point}")
        else:
            st.markdown("No key points available")
        st.markdown("")

        # Follow-up Points
        st.markdown("### 📋 Follow-up Points")
        followup_points = meeting.get('followup_points', [])
        if followup_points:
            for point in followup_points:
                st.markdown(f"• {point}")
        else:
            st.markdown("No follow-up points available")

    with col2:
        # Next Meeting
        st.markdown("### 📅 Next Meeting")
        next_meet = meeting.get('next_meet_schedule')
        if next_meet:
            next_meet_dt = datetime.fromisoformat(next_meet.replace('Z', '+00:00'))
            next_meet_str = next_meet_dt.strftime("%Y-%m-%d at %H:%M")
            st.success(f"📅 {next_meet_str}")
        else:
            st.warning("⏸️ Not scheduled")

def show_edit_form(meeting):
    """Show editable form for meeting"""
    with st.form("edit_meeting_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            new_title = st.text_input("Title", value=meeting.get('title', ''))
            new_summary = st.text_area("Summary", value=meeting.get('summary', ''), height=120)

            key_points_str = ', '.join(meeting.get('key_points', []) or [])
            new_key_points = st.text_area("Key Points (comma/semicolon separated)", value=key_points_str)

            followup_points_str = ', '.join(meeting.get('followup_points', []) or [])
            new_followup_points = st.text_area("Follow-up Points (comma/semicolon separated)", value=followup_points_str)

        with col2:
            next_meet = meeting.get('next_meet_schedule')
            if next_meet:
                next_meet_date = datetime.fromisoformat(next_meet.replace('Z', '+00:00')).date()
                next_meet_time = datetime.fromisoformat(next_meet.replace('Z', '+00:00')).time()
            else:
                next_meet_date = None
                next_meet_time = None

            new_next_date = st.date_input("Next Meeting Date", value=next_meet_date)
            new_next_time = st.time_input("Next Meeting Time", value=next_meet_time)

        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
            # Process and save changes
            key_points_list = [point.strip() for point in new_key_points.replace(';', ',').split(',') if point.strip()]
            followup_points_list = [point.strip() for point in new_followup_points.replace(';', ',').split(',') if point.strip()]

            next_meeting = None
            if new_next_date and new_next_time:
                next_meeting = datetime.combine(new_next_date, new_next_time).isoformat()
            elif new_next_date:
                next_meeting = datetime.combine(new_next_date, datetime.min.time()).isoformat()

            success = update_meeting_simple(
                meeting['id'],
                new_title,
                new_summary,
                key_points_list,
                followup_points_list,
                next_meeting
            )

            if success:
                st.success("Meeting updated successfully!")
                st.session_state.edit_mode = False
                # Update the selected meeting with new data
                updated_meeting = meeting.copy()
                updated_meeting.update({
                    'title': new_title,
                    'summary': new_summary,
                    'key_points': key_points_list,
                    'followup_points': followup_points_list,
                    'next_meet_schedule': next_meeting
                })
                st.session_state.selected_meeting = updated_meeting
                st.rerun()

def show_add_meeting_form():
    """Show add new meeting form"""
    st.markdown('<div class="add-meeting-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-header">🆕 Create New Meeting Record</div>', unsafe_allow_html=True)

    with st.form("add_new_meeting_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            new_title = st.text_input("Meeting Title *", placeholder="Enter meeting title...")
            new_summary = st.text_area("Meeting Summary *", placeholder="Summarize what was discussed...", height=120)
            new_key_points = st.text_area("Key Points (comma/semicolon separated)", placeholder="Key decisions, action items...")
            new_followup_points = st.text_area("Follow-up Points (comma/semicolon separated)", placeholder="Tasks to complete...")

        with col2:
            st.write("**Next Meeting Schedule**")
            next_meeting_date = st.date_input("Date", value=None)
            next_meeting_time = st.time_input("Time", value=datetime.now().time())

            meeting_type = st.selectbox("Meeting Type", ["Manual Entry", "Follow-up Meeting", "Regular Meeting", "Ad-hoc Meeting", "Review Meeting"])
            priority = st.selectbox("Priority Level", ["Medium", "High", "Low", "Critical"])

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submit_clicked = st.form_submit_button("✅ Create Meeting", type="primary", use_container_width=True)
        with col_cancel:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.rerun()

        if submit_clicked:
            if new_title.strip() and new_summary.strip():
                # Process form data
                key_points_list = [point.strip() for point in new_key_points.replace(';', ',').split(',') if point.strip()]
                followup_points_list = [point.strip() for point in new_followup_points.replace(';', ',').split(',') if point.strip()]

                if meeting_type != "Manual Entry":
                    key_points_list.append(f"Meeting Type: {meeting_type}")
                if priority != "Medium":
                    key_points_list.append(f"Priority: {priority}")

                next_meeting = None
                if next_meeting_date and next_meeting_time:
                    next_meeting = datetime.combine(next_meeting_date, next_meeting_time).isoformat()
                elif next_meeting_date:
                    next_meeting = datetime.combine(next_meeting_date, datetime.min.time()).isoformat()

                success = create_new_meeting(new_title.strip(), new_summary.strip(), key_points_list, followup_points_list, next_meeting)

                if success:
                    st.success(f"✅ Meeting '{new_title}' created successfully!")
                    st.session_state.show_add_form = False
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to create meeting")
            else:
                st.error("Please fill in both Title and Summary fields (marked with *)")

    st.markdown('</div>', unsafe_allow_html=True)

def download_transcript(transcript_id):
    """Download transcript file"""
    if not transcript_id:
        st.warning("No transcript linked to this meeting")
        return

    transcript = fetch_transcript_simple(transcript_id)
    if transcript:
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
    """Keep Space Management tab unchanged as requested"""
    st.header("Database Space Management")

    st.subheader("📊 Database Statistics")

    stats = get_stats_cached()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total Meetings", value=stats.get('meetings_count', 0), delta=None)

    with col2:
        st.metric(label="Total Transcripts", value=stats.get('transcripts_count', 0), delta=None)

    with col3:
        st.metric(label="Storage Used (MB)", value=f"{stats.get('total_size_mb', 0):.2f}", delta=None)

    st.subheader("📋 Table Details")

    table_data = pd.DataFrame({
        'Table': ['meetings', 'transcripts'],
        'Record Count': [stats.get('meetings_count', 0), stats.get('transcripts_count', 0)],
        'Size (MB)': [f"{stats.get('meetings_size_mb', 0):.3f}", f"{stats.get('transcripts_size_mb', 0):.3f}"]
    })

    st.dataframe(table_data, use_container_width=True, hide_index=True)

    if st.session_state.cache_timestamp:
        cache_age = (datetime.now() - st.session_state.cache_timestamp).seconds
        st.caption(f"📊 Data refreshed {cache_age} seconds ago")

    st.markdown("---")

    col_refresh = st.columns(1)[0]
    with col_refresh:
        if st.button("🔄 Refresh Stats", help="Manually refresh database statistics"):
            st.session_state.stats_cache = None
            st.session_state.cache_timestamp = None
            st.rerun()

if __name__ == "__main__":
    main()
