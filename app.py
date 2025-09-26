import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import re
import io
from datetime import date

# Try importing optional dependencies
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from supabase_client import *
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Set page configuration for modern look
st.set_page_config(
    page_title="Meeting Manager",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern macOS-style CSS
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Global macOS-style theme */
    .stApp {
        background: #f5f5f7 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #1d1d1f !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header, .viewerBadge_container__1QSob {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Override all text colors */
    .stApp *, .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div {
        color: #1d1d1f !important;
    }
    
    /* Main title - macOS style */
    .main-title {
        font-size: 34px !important;
        font-weight: 700 !important;
        color: #1d1d1f !important;
        text-align: center !important;
        margin: 40px 0 50px 0 !important;
        letter-spacing: -0.5px !important;
    }
    
    /* Tab styling - Clean macOS tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: white !important;
        border-radius: 12px !important;
        padding: 4px !important;
        border: 1px solid #e5e5e7 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08) !important;
        margin-bottom: 32px !important;
        gap: 4px !important;
        justify-content: center !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        color: #6e6e73 !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        transition: all 0.2s ease !important;
        min-width: 120px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: #007aff !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(0,122,255,0.3) !important;
    }
    
    /* Controls section - macOS card style */
    .controls-section {
        background: white !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin-bottom: 24px !important;
        border: 1px solid #e5e5e7 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
    }
    
    /* Meeting cards - Clean macOS style */
    .meeting-card {
        background: white !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin: 12px 0 !important;
        border: 1px solid #e5e5e7 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        position: relative !important;
    }
    
    .meeting-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.12) !important;
        border-color: #007aff !important;
    }
    
    .card-title {
        font-size: 17px !important;
        font-weight: 600 !important;
        color: #1d1d1f !important;
        margin-bottom: 8px !important;
    }
    
    .card-subtitle {
        font-size: 13px !important;
        color: #6e6e73 !important;
        margin-bottom: 4px !important;
        font-weight: 400 !important;
    }
    
    .card-content {
        color: #424245 !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
        margin-top: 8px !important;
    }
    
    /* Buttons - macOS style */
    .stButton > button {
        background: #007aff !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        font-size: 15px !important;
        transition: all 0.2s ease !important;
        font-family: inherit !important;
    }
    
    .stButton > button:hover {
        background: #0056cc !important;
        transform: translateY(-1px) !important;
    }
    
    /* Input fields - macOS style */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: white !important;
        border: 1px solid #d1d1d6 !important;
        border-radius: 8px !important;
        color: #1d1d1f !important;
        font-size: 16px !important;
        padding: 12px 16px !important;
        font-family: inherit !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #007aff !important;
        box-shadow: 0 0 0 3px rgba(0,122,255,0.1) !important;
        outline: none !important;
    }
    
    /* Labels */
    .stTextInput label, .stTextArea label, .stSelectbox label {
        color: #1d1d1f !important;
        font-weight: 500 !important;
        font-size: 15px !important;
        margin-bottom: 6px !important;
    }
    
    /* Metric cards - macOS style */
    .metric-card {
        background: white !important;
        border-radius: 12px !important;
        padding: 24px !important;
        text-align: center !important;
        border: 1px solid #e5e5e7 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
        transition: transform 0.2s ease !important;
    }
    
    .metric-card:hover {
        transform: translateY(-2px) !important;
    }
    
    .metric-title {
        font-size: 13px !important;
        color: #6e6e73 !important;
        margin-bottom: 8px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .metric-value {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #1d1d1f !important;
        letter-spacing: -1px !important;
    }
    
    /* Form styling */
    .stForm {
        background: #f9f9f9 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        border: 1px solid #e5e5e7 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: #007aff !important;
        border-radius: 4px !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: #d4f1d4 !important;
        color: #1b5e20 !important;
        border-left: 4px solid #4caf50 !important;
        border-radius: 8px !important;
    }
    
    .stError {
        background: #ffebee !important;
        color: #c62828 !important;
        border-left: 4px solid #f44336 !important;
        border-radius: 8px !important;
    }
    
    .stWarning {
        background: #fff3e0 !important;
        color: #ef6c00 !important;
        border-left: 4px solid #ff9800 !important;
        border-radius: 8px !important;
    }
    
    .stInfo {
        background: #e3f2fd !important;
        color: #1565c0 !important;
        border-left: 4px solid #2196f3 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_meeting' not in st.session_state:
    st.session_state.selected_meeting = None
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'show_manual_entry' not in st.session_state:
    st.session_state.show_manual_entry = False

# FIXED: Mock functions with different names to avoid recursion
def get_meetings_data():
    """Get meetings from database or return mock data"""
    if SUPABASE_AVAILABLE:
        try:
            # Call the actual supabase function
            response = supabase.table("meetings").select("*, transcripts(meeting_title, audio_url)").order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Database error: {e}")
            return get_mock_meetings()
    else:
        return get_mock_meetings()

def get_mock_meetings():
    """Return mock meeting data for testing"""
    return [{
        'id': '1',
        'title': 'ASAP Register the Company',
        'summary': 'Client wants his company to be registered ASAP. Discussed the process and requirements for private limited company registration.',
        'key_points': ['Register private limited company', 'Prepare required documents', 'File with registrar'],
        'followup_points': ['Send document checklist', 'Schedule follow-up call'],
        'created_at': '2025-09-25T14:45:00',
        'updated_at': '2025-09-25T14:50:00',
        'transcript_id': None
    }]

def get_storage_stats():
    """Get database storage statistics"""
    if SUPABASE_AVAILABLE:
        try:
            meetings_response = supabase.table("meetings").select("id", count="exact").execute()
            meetings_count = meetings_response.count or 0
            
            transcripts_response = supabase.table("transcripts").select("id", count="exact").execute()
            transcripts_count = transcripts_response.count or 0
            
            return {
                'meetings_count': meetings_count,
                'transcripts_count': transcripts_count,
                'meetings_size_mb': meetings_count * 0.01,
                'transcripts_size_mb': transcripts_count * 0.05,
                'total_size_mb': (meetings_count * 0.01) + (transcripts_count * 0.05)
            }
        except Exception as e:
            st.error(f"Database error: {e}")
            return get_mock_stats()
    else:
        return get_mock_stats()

def get_mock_stats():
    """Return mock storage statistics"""
    return {
        'meetings_count': 1,
        'transcripts_count': 0,
        'meetings_size_mb': 0.1,
        'transcripts_size_mb': 0.0,
        'total_size_mb': 0.1
    }

def save_new_meeting(title, summary, key_points, followup_points, next_schedule=None):
    """Save a new meeting to database"""
    if SUPABASE_AVAILABLE:
        try:
            new_meeting_data = {
                "title": title,
                "summary": summary,
                "key_points": key_points,
                "followup_points": followup_points
            }
            if next_schedule:
                new_meeting_data["next_meet_schedule"] = next_schedule
                
            response = supabase.table("meetings").insert(new_meeting_data).execute()
            return True
        except Exception as e:
            st.error(f"Database error: {e}")
            return False
    else:
        st.info(f"Mock save: {title}")
        return True

def create_meeting_card(meeting, index):
    """Create HTML for a meeting card"""
    source = "Automatic" if meeting.get('transcript_id') else "Manual"
    created_date = pd.to_datetime(meeting['created_at']).strftime('%Y-%m-%d %H:%M')
    updated_date = pd.to_datetime(meeting['updated_at']).strftime('%Y-%m-%d %H:%M')
    
    key_points_preview = ""
    if meeting.get('key_points'):
        preview_points = meeting['key_points'][:1]
        key_points_preview = preview_points[0] if preview_points else ""
        if len(meeting['key_points']) > 1:
            key_points_preview += f" (+{len(meeting['key_points']) - 1} more)"
    
    card_html = f"""
    <div class="meeting-card">
        <div class="card-title">📋 {meeting.get('title', 'Untitled Meeting')}</div>
        <div class="card-subtitle">📍 Source: {source} • 📅 Created: {created_date}</div>
        <div class="card-subtitle">🔄 Updated: {updated_date}</div>
        <div class="card-content">🔑 {key_points_preview}</div>
    </div>
    """
    return card_html

def show_meeting_details_popup(meeting):
    """Show meeting details in a popup modal"""
    if not meeting:
        return
    
    with st.container():
        st.markdown("---")
        st.markdown("### 📋 Meeting Details")
        
        # Header with close button
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("❌ Close", key="close_popup"):
                st.session_state.show_popup = False
                st.rerun()
        
        # Meeting information
        source = "Automatic" if meeting.get('transcript_id') else "Manual"
        created_date = pd.to_datetime(meeting['created_at']).strftime('%Y-%m-%d %H:%M')
        updated_date = pd.to_datetime(meeting['updated_at']).strftime('%Y-%m-%d %H:%M')
        
        st.markdown(f"**📝 Title:** {meeting.get('title', 'N/A')}")
        st.markdown(f"**📍 Source:** {source}")
        st.markdown(f"**📅 Created:** {created_date}")
        st.markdown(f"**🔄 Updated:** {updated_date}")
        
        st.markdown("**📋 Summary:**")
        st.write(meeting.get('summary', 'No summary available'))
        
        st.markdown("**🔑 Key Points:**")
        key_points = meeting.get('key_points', [])
        if key_points:
            for i, point in enumerate(key_points, 1):
                st.write(f"{i}. {point}")
        else:
            st.write("No key points available")
        
        st.markdown("**📝 Follow-up Points:**")
        followup_points = meeting.get('followup_points', [])
        if followup_points:
            for i, point in enumerate(followup_points, 1):
                st.write(f"{i}. {point}")
        else:
            st.write("No follow-up points available")
        
        # Action buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✏️ Edit Meeting", key="edit_meeting"):
                st.info("Edit functionality coming soon!")
        with col2:
            if st.button("📤 Export", key="export_meeting"):
                st.info("Export functionality coming soon!")
        
        st.markdown("---")

def meeting_details_tab():
    """Main meeting details tab content"""
    # Controls section
    st.markdown('<div class="controls-section">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search meetings", placeholder="Search by title or content...", label_visibility="collapsed")
    
    with col2:
        date_filter = st.selectbox("📅 Filter by Date", ["All", "Today", "This Week", "This Month"], label_visibility="collapsed")
    
    with col3:
        if st.button("➕ Manual Entry", key="manual_entry_btn"):
            st.session_state.show_manual_entry = True
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show manual entry form if requested
    if st.session_state.get('show_manual_entry', False):
        show_manual_entry_form()
        return
    
    # Fetch meetings using the fixed function
    meetings = get_meetings_data()
    
    if not meetings:
        st.info("🎯 No meetings found. Use the Manual Entry button to add your first meeting.")
        return
    
    st.markdown(f"### Found {len(meetings)} meeting(s)")
    
    # Display meeting cards
    for index, meeting in enumerate(meetings):
        card_html = create_meeting_card(meeting, index)
        st.markdown(card_html, unsafe_allow_html=True)
        
        # View details button
        if st.button(f"👁️ View Details", key=f"view_meeting_{index}"):
            st.session_state.selected_meeting = meeting
            st.session_state.show_popup = True
            st.rerun()
    
    # Show popup if meeting is selected
    if st.session_state.show_popup and st.session_state.selected_meeting:
        show_meeting_details_popup(st.session_state.selected_meeting)

def show_manual_entry_form():
    """Show the manual meeting entry form"""
    st.markdown("### ✏️ Manual Meeting Entry")
    
    with st.form("manual_entry_form", clear_on_submit=True):
        title = st.text_input("Meeting Title*", placeholder="Enter meeting title")
        summary = st.text_area("Meeting Summary*", placeholder="Enter meeting summary", height=100)
        
        st.write("**Key Points:**")
        key_point_1 = st.text_input("Key Point 1", placeholder="First key point")
        key_point_2 = st.text_input("Key Point 2", placeholder="Second key point")
        key_point_3 = st.text_input("Key Point 3", placeholder="Third key point")
        
        st.write("**Follow-up Points:**")
        followup_1 = st.text_input("Follow-up Point 1", placeholder="First follow-up point")
        followup_2 = st.text_input("Follow-up Point 2", placeholder="Second follow-up point")
        
        next_meeting_date = st.date_input("Next Meeting Date (Optional)")
        
        # Form buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Meeting")
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_manual_entry = False
                st.rerun()
        
        if submitted:
            if title and summary:
                # Prepare data
                key_points = [point for point in [key_point_1, key_point_2, key_point_3] if point.strip()]
                followup_points = [point for point in [followup_1, followup_2] if point.strip()]
                next_schedule = next_meeting_date.isoformat() if next_meeting_date else None
                
                # Save meeting
                success = save_new_meeting(title, summary, key_points, followup_points, next_schedule)
                
                if success:
                    st.success("✅ Meeting saved successfully!")
                    st.session_state.show_manual_entry = False
                    st.rerun()
                else:
                    st.error("❌ Error saving meeting. Please try again.")
            else:
                st.error("❌ Please fill in the required fields (Title and Summary)")

def space_management_tab():
    """Space management tab content"""
    st.markdown("## 💾 Space Management")
    
    # Get storage statistics using the fixed function
    stats = get_storage_stats()
    
    st.markdown("### Storage Overview")
    
    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Meetings</div>
            <div class="metric-value">{stats['meetings_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Transcripts</div>
            <div class="metric-value">{stats['transcripts_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Storage Used</div>
            <div class="metric-value">{stats['total_size_mb']:.1f} MB</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        remaining = max(1024 - stats['total_size_mb'], 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Available</div>
            <div class="metric-value">{remaining:.1f} MB</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Storage usage progress
    st.markdown("### Storage Usage")
    progress_value = min(stats['total_size_mb'] / 1024, 1.0)
    st.progress(progress_value)
    st.markdown(f"**{stats['total_size_mb']:.1f} MB of 1024 MB used ({progress_value*100:.1f}%)**")
    
    # Storage breakdown chart
    if PLOTLY_AVAILABLE:
        st.markdown("### Storage Breakdown")
        fig = go.Figure(data=[
            go.Bar(name='Meetings', x=['Storage'], y=[stats['meetings_size_mb']]),
            go.Bar(name='Transcripts', x=['Storage'], y=[stats['transcripts_size_mb']])
        ])
        fig.update_layout(
            barmode='stack',
            title="Storage Usage by Data Type",
            yaxis_title="Size (MB)",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Install Plotly to see storage breakdown chart")

def main():
    """Main application function"""
    # App title
    st.markdown('<h1 class="main-title">📋 Meeting Manager</h1>', unsafe_allow_html=True)
    
    # Show dependency status
    if not SUPABASE_AVAILABLE:
        st.warning("⚠️ Database not connected - Using mock data")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 Meeting Details", "💾 Space Management"])
    
    with tab1:
        meeting_details_tab()
    
    with tab2:
        space_management_tab()

if __name__ == "__main__":
    main()
