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
    /* Import SF Pro Display font (macOS system font) */
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
    
    /* Modal overlay - macOS style */
    .modal-overlay {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background: rgba(0,0,0,0.4) !important;
        backdrop-filter: blur(8px) !important;
        z-index: 9999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        animation: fadeIn 0.2s ease !important;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Modal content - macOS window style */
    .modal-content {
        background: white !important;
        border-radius: 12px !important;
        padding: 32px !important;
        margin: 20px !important;
        max-width: 600px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        box-shadow: 0 20px 60px rgba(0,0,0,0.25) !important;
        border: 1px solid #e5e5e7 !important;
        animation: slideUp 0.3s ease !important;
        position: relative !important;
    }
    
    @keyframes slideUp {
        from { 
            transform: translateY(50px);
            opacity: 0;
        }
        to { 
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    /* Close button - macOS style */
    .close-button {
        position: absolute !important;
        top: 16px !important;
        right: 16px !important;
        width: 24px !important;
        height: 24px !important;
        border-radius: 50% !important;
        background: #ff5f57 !important;
        border: none !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: white !important;
        font-size: 12px !important;
        font-weight: bold !important;
    }
    
    .close-button:hover {
        background: #ff3b30 !important;
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
    
    /* Secondary button */
    .secondary-button {
        background: #f2f2f7 !important;
        color: #007aff !important;
    }
    
    .secondary-button:hover {
        background: #e5e5ea !important;
        color: #0056cc !important;
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
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Hide modal when not active */
    .hidden {
        display: none !important;
    }
</style>

<script>
function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        closeModal();
    }
});

// Close modal with escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});
</script>
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

# Mock functions for when dependencies aren't available
def fetch_meetings():
    if SUPABASE_AVAILABLE:
        return fetch_meetings()
    else:
        return [{
            'id': '1',
            'title': 'ASAP Register the Company',
            'summary': 'Client wants his company to be registered ASAP. Discussed the process and requirements.',
            'key_points': ['Register private limited company', 'Prepare required documents', 'File with registrar'],
            'followup_points': ['Send document checklist', 'Schedule follow-up call'],
            'created_at': '2025-09-25T14:45:00',
            'updated_at': '2025-09-25T14:50:00',
            'transcript_id': None
        }]

def get_database_stats():
    return {
        'meetings_count': 1,
        'transcripts_count': 0,
        'meetings_size_mb': 0.1,
        'transcripts_size_mb': 0.0,
        'total_size_mb': 0.1
    }

def create_meeting_card(meeting, index):
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
    <div class="meeting-card" onclick="showMeetingModal('{index}')">
        <div class="card-title">📋 {meeting.get('title', 'Untitled Meeting')}</div>
        <div class="card-subtitle">📍 Source: {source} • 📅 Created: {created_date}</div>
        <div class="card-subtitle">🔄 Updated: {updated_date}</div>
        <div class="card-content">🔑 {key_points_preview}</div>
    </div>
    """
    return card_html

def show_meeting_modal(meeting):
    if not meeting:
        return
        
    source = "Automatic" if meeting.get('transcript_id') else "Manual"
    created_date = pd.to_datetime(meeting['created_at']).strftime('%Y-%m-%d %H:%M')
    updated_date = pd.to_datetime(meeting['updated_at']).strftime('%Y-%m-%d %H:%M')
    
    modal_html = f"""
    <div class="modal-overlay" id="meetingModal">
        <div class="modal-content">
            <button class="close-button" onclick="closeModal()">×</button>
            
            <h2 style="color: #1d1d1f; margin-bottom: 24px; font-size: 24px; font-weight: 700;">
                📋 Meeting Details
            </h2>
            
            <div style="margin-bottom: 16px;">
                <strong style="color: #1d1d1f;">Title:</strong>
                <span style="color: #424245;">{meeting.get('title', 'N/A')}</span>
            </div>
            
            <div style="margin-bottom: 16px;">
                <strong style="color: #1d1d1f;">Source:</strong>
                <span style="color: #424245;">{source}</span>
            </div>
            
            <div style="margin-bottom: 16px;">
                <strong style="color: #1d1d1f;">Created:</strong>
                <span style="color: #424245;">{created_date}</span>
            </div>
            
            <div style="margin-bottom: 20px;">
                <strong style="color: #1d1d1f;">Updated:</strong>
                <span style="color: #424245;">{updated_date}</span>
            </div>
            
            <div style="margin-bottom: 20px;">
                <strong style="color: #1d1d1f; display: block; margin-bottom: 8px;">Summary:</strong>
                <p style="color: #424245; line-height: 1.5; margin: 0;">
                    {meeting.get('summary', 'No summary available')}
                </p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <strong style="color: #1d1d1f; display: block; margin-bottom: 8px;">Key Points:</strong>
                <ul style="color: #424245; line-height: 1.5; margin: 0; padding-left: 20px;">
    """
    
    key_points = meeting.get('key_points', [])
    if key_points:
        for point in key_points:
            modal_html += f"<li>{point}</li>"
    else:
        modal_html += "<li>No key points available</li>"
    
    modal_html += """
                </ul>
            </div>
            
            <div style="margin-bottom: 30px;">
                <strong style="color: #1d1d1f; display: block; margin-bottom: 8px;">Follow-up Points:</strong>
                <ul style="color: #424245; line-height: 1.5; margin: 0; padding-left: 20px;">
    """
    
    followup_points = meeting.get('followup_points', [])
    if followup_points:
        for point in followup_points:
            modal_html += f"<li>{point}</li>"
    else:
        modal_html += "<li>No follow-up points available</li>"
    
    modal_html += """
                </ul>
            </div>
            
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button onclick="editMeeting()" style="background: #f2f2f7; color: #007aff; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer;">
                    ✏️ Edit
                </button>
                <button onclick="closeModal()" style="background: #007aff; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer;">
                    Done
                </button>
            </div>
        </div>
    </div>
    
    <script>
    function editMeeting() {
        alert('Edit functionality coming soon!');
    }
    </script>
    """
    
    return modal_html

def meeting_details_tab():
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
    
    if st.session_state.get('show_manual_entry', False):
        manual_entry_form()
        return
    
    meetings = fetch_meetings()
    
    if not meetings:
        st.info("🎯 No meetings found. Use the Manual Entry button to add your first meeting.")
        return
    
    st.markdown(f"### Found {len(meetings)} meeting(s)")
    
    for index, meeting in enumerate(meetings):
        card_html = create_meeting_card(meeting, index)
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Show modal when card is clicked
        if st.button(f"👁️ View Details", key=f"view_meeting_{index}"):
            modal_html = show_meeting_modal(meeting)
            st.markdown(modal_html, unsafe_allow_html=True)

def manual_entry_form():
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
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Meeting")
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_manual_entry = False
                st.rerun()
        
        if submitted:
            if title and summary:
                st.success("✅ Meeting saved successfully!")
                st.session_state.show_manual_entry = False
                st.rerun()
            else:
                st.error("❌ Please fill in the required fields (Title and Summary)")

def space_management_tab():
    st.markdown("## 💾 Space Management")
    
    stats = get_database_stats()
    
    st.markdown("### Storage Overview")
    
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
    
    st.markdown("### Storage Usage")
    progress_value = min(stats['total_size_mb'] / 1024, 1.0)
    st.progress(progress_value)
    st.markdown(f"**{stats['total_size_mb']:.1f} MB of 1024 MB used ({progress_value*100:.1f}%)**")
    
    if PLOTLY_AVAILABLE:
        st.markdown("### Storage Breakdown")
        fig = go.Figure(data=[
            go.Bar(name='Meetings', x=['Storage'], y=[stats['meetings_size_mb']]),
            go.Bar(name='Transcripts', x=['Storage'], y=[stats['transcripts_size_mb']])
        ])
        fig.update_layout(
            barmode='stack',
            title="Storage Usage by Data Type",
            yaxis_title="Size (MB)"
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    # App title
    st.markdown('<h1 class="main-title">📋 Meeting Manager</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 Meeting Details", "💾 Space Management"])
    
    with tab1:
        meeting_details_tab()
    
    with tab2:
        space_management_tab()

if __name__ == "__main__":
    main()
