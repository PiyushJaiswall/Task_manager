import streamlit as st
from datetime import datetime, date
import pandas as pd

# Your existing Supabase client wrapper
from supabase_client import supabase

# Configure Streamlit page
st.set_page_config(
    page_title="Meeting Transcript Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Complete CSS for your exact layout
st.markdown("""
<style>
    /* Dark theme background */
    .main .block-container {
        background-color: #1a202c;
        color: #e2e8f0;
        padding: 1.2rem 2rem;
        font-family: 'Segoe UI', sans-serif;
    }

    h1, h2, h3, h4, h5 {
        color: #e2e8f0;
        margin: 0;
    }

    /* Top controls row */
    .top-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }

    /* Grey curved rectangles for meeting previews */
    .meeting-preview {
        background: linear-gradient(135deg, #f7fafc 0%, #e2e8f0 100%);
        border: 2px solid #cbd5e0;
        border-radius: 12px;
        width: calc(20% - 1rem);
        height: 140px;
        padding: 1rem;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.25s ease;
        box-sizing: border-box;
        display: inline-block;
        vertical-align: top;
        position: relative;
        overflow: hidden;
    }

    .meeting-preview:hover {
        transform: translateY(-4px);
        border-color: #60a5fa;
        box-shadow: 0 8px 22px rgba(96, 165, 250, 0.35);
    }

    .preview-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #1a202c;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 0.5rem;
    }

    .preview-source {
        font-size: 0.75rem;
        color: #4a5568;
        margin: 0.3rem 0;
    }

    .preview-dates {
        font-size: 0.7rem;
        color: #718096;
        line-height: 1.25;
        position: absolute;
        bottom: 0.6rem;
        left: 1rem;
        right: 1rem;
    }

    /* Modal popup (2.5x bigger) */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .modal-content {
        background: #ffffff;
        color: #1a202c;
        border-radius: 16px;
        width: 90%;
        max-width: 1000px;
        max-height: 85vh;
        overflow-y: auto;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        position: relative;
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.2rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }

    .modal-header h2 {
        font-size: 1.4rem;
        font-weight: 800;
        margin: 0;
        color: #1a202c;
    }

    .btn {
        border: none;
        border-radius: 8px;
        padding: 0.45rem 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-edit {
        background: #4299e1;
        color: #fff;
        margin-right: 0.8rem;
    }

    .btn-close {
        background: #f56565;
        color: #fff;
    }

    .section {
        margin-bottom: 1.5rem;
    }

    .section h4 {
        font-weight: 700;
        margin-bottom: 0.4rem;
        font-size: 1.05rem;
        color: #2d3748;
    }

    .content-box {
        background: #f8f9fa;
        border: 1px solid #cbd5e0;
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Add meeting form */
    .add-form {
        background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
        border: 2px solid #38b2ac;
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        color: #1a202c;
    }

    .form-header {
        background: linear-gradient(90deg, #38b2ac 0%, #319795 100%);
        color: #fff;
        border-radius: 14px 14px 0 0;
        margin: -2rem -2rem 2rem -2rem;
        text-align: center;
        padding: 1rem 0;
        font-weight: 700;
        font-size: 1.2rem;
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

    /* Stats boxes for space management */
    div[data-testid="metric-container"] {
        background: #ffffff;
        color: #1a202c;
        border: 2px solid #cbd5e0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Hide empty containers */
    .element-container:empty {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'selected_meeting' not in st.session_state:
    st.session_state.selected_meeting = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Helper functions
@st.cache_data(ttl=30)
def fetch_meetings():
    """Fetch meetings from Supabase with caching"""
    try:
        response = supabase.table("meetings").select("*, transcripts(meeting_title, audio_url)").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching meetings: {str(e)}")
        return []

def format_datetime(ts):
    """Format datetime string for display"""
    if not ts:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return "Unknown"

def create_meeting(title, summary, key_points, followup_points, next_meeting=None):
    """Create new meeting in database"""
    try:
        meeting_data = {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "followup_points": followup_points
        }
        if next_meeting:
            meeting_data["next_meet_schedule"] = next_meeting

        response = supabase.table("meetings").insert(meeting_data).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error creating meeting: {str(e)}")
        return False

def update_meeting(meeting_id, title, summary, key_points, followup_points, next_meeting=None):
    """Update existing meeting in database"""
    try:
        update_data = {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "followup_points": followup_points
        }
        if next_meeting:
            update_data["next_meet_schedule"] = next_meeting

        response = supabase.table("meetings").update(update_data).eq("id", meeting_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating meeting: {str(e)}")
        return False

def get_transcript(transcript_id):
    """Fetch transcript text"""
    try:
        response = supabase.table("transcripts").select("transcript_text").eq("id", transcript_id).execute()
        return response.data[0]["transcript_text"] if response.data else None
    except:
        return None

# Main UI
def main():
    st.title("📝 Meeting Transcript Manager")

    # Create tabs
    tab_details, tab_space = st.tabs(["📋 Meet Details", "🗄️ Space Management"])

    with tab_details:
        meet_details_tab()

    with tab_space:
        space_management_tab()

def meet_details_tab():
    """Meet Details tab with your exact layout"""

    # Top controls row
    col_add, col_search, col_filter, col_refresh = st.columns([1.5, 3, 1.2, 1])

    with col_add:
        if st.button("➕ Add Manual Meeting", use_container_width=True, type="primary"):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.rerun()

    with col_search:
        search_query = st.text_input("Search meetings by title or summary", placeholder="Type to search...")

    with col_filter:
        date_filter = st.date_input("Filter by created date", value=None)

    with col_refresh:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Add meeting form (when toggled)
    if st.session_state.show_add_form:
        show_add_form()

    # Fetch and filter meetings
    meetings = fetch_meetings()

    if search_query:
        meetings = [m for m in meetings 
                   if search_query.lower() in (m.get('title', '') or '').lower() 
                   or search_query.lower() in (m.get('summary', '') or '').lower()]

    if date_filter:
        meetings = [m for m in meetings 
                   if m.get('created_at') and 
                   datetime.fromisoformat(m['created_at'].replace('Z', '+00:00')).date() == date_filter]

    if not meetings:
        st.info("📭 No meetings found in the database.")
        return

    st.write(f"Found {len(meetings)} meeting(s)")
    st.write("")  # Add space

    # Display meeting preview rectangles (5 per row)
    for i, meeting in enumerate(meetings):
        if i % 5 == 0:  # New row every 5 meetings
            cols = st.columns(5)

        with cols[i % 5]:
            display_meeting_preview(meeting)

    # Show detail modal if a meeting is selected
    if st.session_state.selected_meeting:
        show_meeting_modal()

def display_meeting_preview(meeting):
    """Display grey curved rectangle preview"""
    # Format data
    title = meeting.get('title', 'Untitled Meeting')
    source_icon = "📝" if not meeting.get('transcript_id') else "🎤"
    source_type = "Manual" if not meeting.get('transcript_id') else "Transcript"
    created = format_datetime(meeting.get('created_at'))
    updated = format_datetime(meeting.get('updated_at'))

    # Truncate title for display
    display_title = title[:25] + ('...' if len(title) > 25 else '')

    # Create preview button
    preview_content = f"""**{source_icon} {display_title}**
📋 {source_type}
📅 Created: {created}
🔄 Updated: {updated}"""

    if st.button(preview_content, key=f"preview_{meeting['id']}", 
                help="Click to view full details", use_container_width=True):
        st.session_state.selected_meeting = meeting
        st.session_state.edit_mode = False
        st.rerun()

def show_meeting_modal():
    """Show detailed meeting modal (2.5x bigger popup)"""
    meeting = st.session_state.selected_meeting

    st.markdown("---")
    st.markdown("## 📋 Meeting Details")

    # Modal header with Edit and Close buttons
    col_title, col_edit, col_close = st.columns([6, 1, 1])

    with col_title:
        source_icon = "📝" if not meeting.get('transcript_id') else "🎤"
        st.markdown(f"### {source_icon} {meeting.get('title', 'Untitled Meeting')}")

    with col_edit:
        edit_label = "✏️ Edit" if not st.session_state.edit_mode else "👁️ View"
        if st.button(edit_label, key="toggle_edit_mode", use_container_width=True):
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
    source_type = "Manual Entry" if not meeting.get('transcript_id') else "From Transcript"
    created = format_datetime(meeting.get('created_at'))
    updated = format_datetime(meeting.get('updated_at'))

    # Display metadata
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        st.info(f"📋 **Source:** {source_type}")
        st.info(f"📅 **Created:** {created}")
    with col_meta2:
        st.info(f"🔄 **Updated:** {updated}")
        # Transcript download if available
        if meeting.get('transcript_id'):
            if st.button("📄 Download Transcript", key="download_transcript"):
                transcript_text = get_transcript(meeting.get('transcript_id'))
                if transcript_text:
                    st.download_button(
                        label="📥 Download",
                        data=transcript_text,
                        file_name=f"{meeting.get('title', 'meeting')}_transcript.txt",
                        mime="text/plain"
                    )

    st.markdown("---")

    # Content sections
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Title
        st.markdown("### 📝 Title")
        st.markdown(f"**{meeting.get('title', 'Untitled Meeting')}**")
        st.markdown("")

        # Summary
        st.markdown("### 📄 Summary")
        st.markdown(meeting.get('summary', 'No summary available'))
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

    with col_side:
        # Next Meeting
        st.markdown("### 📅 Next Meeting")
        next_meeting = meeting.get('next_meet_schedule')
        if next_meeting:
            next_dt = format_datetime(next_meeting)
            st.success(f"📅 {next_dt}")
        else:
            st.warning("⏸️ Not scheduled")

def show_edit_form(meeting):
    """Show editable form for meeting"""
    with st.form("edit_meeting_form"):
        col_main, col_side = st.columns([2, 1])

        with col_main:
            new_title = st.text_input("Title", value=meeting.get('title', ''))
            new_summary = st.text_area("Summary", value=meeting.get('summary', ''), height=120)

            # Key points
            key_points_str = ', '.join(meeting.get('key_points', []) or [])
            new_key_points = st.text_area("Key Points (comma-separated)", value=key_points_str)

            # Follow-up points
            followup_points_str = ', '.join(meeting.get('followup_points', []) or [])
            new_followup_points = st.text_area("Follow-up Points (comma-separated)", value=followup_points_str)

        with col_side:
            # Next meeting scheduling
            next_meeting = meeting.get('next_meet_schedule')
            if next_meeting:
                next_dt = datetime.fromisoformat(next_meeting.replace('Z', '+00:00'))
                default_date = next_dt.date()
                default_time = next_dt.time()
            else:
                default_date = None
                default_time = datetime.now().time()

            new_next_date = st.date_input("Next Meeting Date", value=default_date)
            new_next_time = st.time_input("Next Meeting Time", value=default_time)

        # Save button
        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
            # Process form data
            key_points_list = [point.strip() for point in new_key_points.replace(';', ',').split(',') if point.strip()]
            followup_points_list = [point.strip() for point in new_followup_points.replace(';', ',').split(',') if point.strip()]

            next_meeting_schedule = None
            if new_next_date:
                next_meeting_schedule = datetime.combine(new_next_date, new_next_time).isoformat()

            # Update meeting
            success = update_meeting(
                meeting['id'],
                new_title,
                new_summary,
                key_points_list,
                followup_points_list,
                next_meeting_schedule
            )

            if success:
                st.success("Meeting updated successfully!")
                # Update the selected meeting data
                updated_meeting = meeting.copy()
                updated_meeting.update({
                    'title': new_title,
                    'summary': new_summary,
                    'key_points': key_points_list,
                    'followup_points': followup_points_list,
                    'next_meet_schedule': next_meeting_schedule
                })
                st.session_state.selected_meeting = updated_meeting
                st.session_state.edit_mode = False
                st.rerun()

def show_add_form():
    """Show add new meeting form"""
    with st.form("add_meeting_form"):
        st.markdown('<div class="form-header">🆕 Create New Meeting Record</div>', unsafe_allow_html=True)

        col_main, col_side = st.columns([2, 1])

        with col_main:
            title = st.text_input("Meeting Title *", placeholder="Enter meeting title...")
            summary = st.text_area("Meeting Summary *", placeholder="Summarize what was discussed...", height=120)
            key_points = st.text_area("Key Points (comma-separated)", placeholder="Key decisions, action items...")
            followup_points = st.text_area("Follow-up Points (comma-separated)", placeholder="Tasks to complete...")

        with col_side:
            st.write("**Next Meeting Schedule**")
            next_date = st.date_input("Date", value=None)
            next_time = st.time_input("Time", value=datetime.now().time())

            meeting_type = st.selectbox("Meeting Type", 
                ["Manual Entry", "Follow-up Meeting", "Regular Meeting", "Ad-hoc Meeting", "Review Meeting"])
            priority = st.selectbox("Priority Level", ["Medium", "High", "Low", "Critical"])

        # Form buttons
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("✅ Create Meeting", type="primary", use_container_width=True)
        with col_cancel:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.rerun()

        # Handle form submission
        if submitted:
            if not title.strip() or not summary.strip():
                st.error("Please fill in both Title and Summary fields (marked with *)")
            else:
                # Process form data
                key_points_list = [point.strip() for point in key_points.replace(';', ',').split(',') if point.strip()]
                followup_points_list = [point.strip() for point in followup_points.replace(';', ',').split(',') if point.strip()]

                # Add metadata
                if meeting_type != "Manual Entry":
                    key_points_list.append(f"Meeting Type: {meeting_type}")
                if priority != "Medium":
                    key_points_list.append(f"Priority: {priority}")

                # Next meeting schedule
                next_meeting_schedule = None
                if next_date:
                    next_meeting_schedule = datetime.combine(next_date, next_time).isoformat()

                # Create meeting
                success = create_meeting(
                    title.strip(),
                    summary.strip(),
                    key_points_list,
                    followup_points_list,
                    next_meeting_schedule
                )

                if success:
                    st.success(f"✅ Meeting '{title}' created successfully!")
                    st.session_state.show_add_form = False
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to create meeting")

def space_management_tab():
    """Space Management tab (unchanged as requested)"""
    st.header("Database Space Management")

    st.subheader("📊 Database Statistics")

    try:
        # Get stats
        meetings_response = supabase.table("meetings").select("id", count="exact").execute()
        transcripts_response = supabase.table("transcripts").select("id", count="exact").execute()

        meetings_count = meetings_response.count or 0
        transcripts_count = transcripts_response.count or 0

        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Meetings", meetings_count)

        with col2:
            st.metric("Total Transcripts", transcripts_count)

        with col3:
            total_size = (meetings_count * 0.01) + (transcripts_count * 0.05)
            st.metric("Storage Used (MB)", f"{total_size:.2f}")

        # Table details
        st.subheader("📋 Table Details")

        table_data = pd.DataFrame({
            'Table': ['meetings', 'transcripts'],
            'Record Count': [meetings_count, transcripts_count],
            'Size (MB)': [f"{meetings_count * 0.01:.3f}", f"{transcripts_count * 0.05:.3f}"]
        })

        st.dataframe(table_data, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

    st.markdown("---")

    # Additional tools
    st.subheader("🧹 Database Management")
    st.info("💡 Additional management tools can be added here for data cleanup, export, etc.")

    if st.button("🔄 Refresh Statistics"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()
