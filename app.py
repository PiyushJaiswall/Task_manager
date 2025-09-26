import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from supabase_client import *
from transformers import pipeline
import json
import re
import io
from datetime import date
import base64

# FORCE page configuration to override theme
st.set_page_config(
    page_title="Meeting Manager",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
/* =========================== */
/*      Global App Settings    */
/* =========================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

.stApp {
    background-color: #0d1117 !important;
    color: #f0f6fc !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Hide Streamlit default UI */
#MainMenu, footer, header, .viewerBadge_container__1QSob {
    visibility: hidden !important;
    display: none !important;
}

/* General text colors */
.stApp *, .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div {
    color: #f0f6fc !important;
}

/* =========================== */
/*       Main Title Style      */
/* =========================== */
.main-title {
    font-size: 34px !important;
    font-weight: 700 !important;
    color: #f0f6fc !important;
    text-align: center !important;
    margin: 40px 0 50px 0 !important;
    letter-spacing: -0.5px !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
}

/* =========================== */
/*        Tabs Styling         */
/* =========================== */
.stTabs [data-baseweb="tab-list"] {
    background-color: #21262d !important; /* subtle dark gray for tab container */
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid #30363d !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    margin-bottom: 32px !important;
    gap: 4px !important;
    justify-content: center !important;
}

.stTabs [data-baseweb="tab"] {
    background: #161b22 !important;
    color: #c9d1d9 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 16px !important;
    padding: 12px 24px !important;
    min-width: 120px !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background: #0969da !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(9,105,218,0.4) !important;
}

/* =========================== */
/*       Card Styling          */
/* =========================== */
.controls-section, .meeting-card, .metric-card, .stForm {
    background-color: #161b22 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    border: 1px solid #30363d !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
    transition: all 0.2s ease !important;
}

.meeting-card:hover, .metric-card:hover {
    transform: translateY(-2px) !important;
    background-color: #1c2128 !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important;
    border-color: #0969da !important;
}

.card-title {
    font-size: 17px !important;
    font-weight: 600 !important;
    color: #f0f6fc !important;
    margin-bottom: 8px !important;
}

.card-subtitle {
    font-size: 13px !important;
    color: #8b949e !important;
    margin-bottom: 4px !important;
}

.card-content {
    font-size: 14px !important;
    color: #c9d1d9 !important;
    line-height: 1.4 !important;
    margin-top: 8px !important;
}

/* =========================== */
/*       Buttons Styling       */
/* =========================== */
.stButton > button {
    background-color: #0969da !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 10px 20px !important;
    font-family: inherit !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background-color: #0860ca !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(9,105,218,0.3) !important;
}

/* =========================== */
/*       Input Fields          */
/* =========================== */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #f0f6fc !important;
    font-size: 16px !important;
    padding: 12px 16px !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #0969da !important;
    box-shadow: 0 0 0 3px rgba(9,105,218,0.1) !important;
    outline: none !important;
}

.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #6e7681 !important;
}

.stTextInput label, .stTextArea label, .stSelectbox label {
    color: #f0f6fc !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    margin-bottom: 6px !important;
}

/* =========================== */
/*       Scrollbar Styling     */
/* =========================== */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background-color: #161b22;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background-color: #30363d;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background-color: #484f58;
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
if 'summarizer' not in st.session_state:
    try:
        # Only show model loading message once
        with st.spinner("Loading AI model..."):
            st.session_state.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    except Exception as e:
        st.error(f"Error loading summarization model: {e}")
        st.session_state.summarizer = None

# Helper functions (same as before)
def extract_key_points(text, num_points=5):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    key_sentences = sorted(sentences, key=len, reverse=True)[:num_points]
    return key_sentences

def extract_followup_points(text):
    followup_keywords = ['follow up', 'next steps', 'action items', 'todo', 'will discuss', 'next meeting', 'review']
    followup_points = []
    sentences = re.split(r'[.!?]+', text.lower())
    for sentence in sentences:
        if any(keyword in sentence for keyword in followup_keywords):
            followup_points.append(sentence.strip().capitalize())
    return followup_points[:3] if followup_points else ["Review meeting outcomes", "Schedule follow-up discussion"]

def extract_next_meeting_schedule(text):
    date_patterns = [
        r'next (monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday) next week',
        r'in (\\d+) days?',
        r'next month',
        r'next week'
    ]
    text_lower = text.lower()
    for pattern in date_patterns:
        if re.search(pattern, text_lower):
            return (datetime.now() + timedelta(days=7)).isoformat()
    return None

def process_transcript_for_meeting(transcript_data):
    if not transcript_data or not transcript_data.get('transcript_text'):
        return None
    
    transcript_text = transcript_data['transcript_text']
    summary = ""
    
    if st.session_state.summarizer and len(transcript_text) > 100:
        try:
            summary_result = st.session_state.summarizer(transcript_text, max_length=150, min_length=50, do_sample=False)
            summary = summary_result[0]['summary_text']
        except Exception as e:
            summary = transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text
    else:
        summary = transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text
    
    key_points = extract_key_points(transcript_text)
    followup_points = extract_followup_points(transcript_text)
    next_schedule = extract_next_meeting_schedule(transcript_text)
    
    return {
        'title': transcript_data.get('meeting_title', 'Untitled Meeting'),
        'summary': summary,
        'key_points': key_points,
        'followup_points': followup_points,
        'next_meet_schedule': next_schedule,
        'transcript_id': transcript_data['id']
    }

def create_meeting_card(meeting, index):
    source = "🤖 Automatic" if meeting.get('transcript_id') else "✍️ Manual"
    created_date = pd.to_datetime(meeting['created_at']).strftime('%Y-%m-%d %H:%M')
    updated_date = pd.to_datetime(meeting['updated_at']).strftime('%Y-%m-%d %H:%M')
    
    key_points_preview = ""
    if meeting.get('key_points'):
        preview_points = meeting['key_points'][:2]
        key_points_preview = " • ".join([point[:50] + "..." if len(point) > 50 else point for point in preview_points])
        if len(meeting['key_points']) > 2:
            key_points_preview += f" • +{len(meeting['key_points']) - 2} more"
    
    card_html = f"""
    <div class="meeting-card" id="meeting-{index}">
        <div class="card-title">📋 {meeting.get('title', 'Untitled Meeting')}</div>
        <div class="card-subtitle">{source} • 📅 Created: {created_date}</div>
        <div class="card-subtitle">🔄 Updated: {updated_date}</div>
        {f'<div class="card-content">🔑 Key Points: {key_points_preview}</div>' if key_points_preview else ''}
    </div>
    """
    return card_html

def show_meeting_popup(meeting):
    """Show meeting details in a floating modal-like overlay."""
    
    if "show_popup" not in st.session_state:
        st.session_state.show_popup = False
        st.session_state.edit_mode = False

    # Only render the popup if triggered
    if not st.session_state.show_popup:
        return

    # Modal overlay
    st.markdown("""
    <style>
    .modal-background {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(0,0,0,0.6);
        z-index: 9998;
    }
    .modal-content {
        position: fixed;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        background-color: #161b22;
        color: #f0f6fc;
        padding: 30px;
        border-radius: 12px;
        width: 60%;
        max-height: 80%;
        overflow-y: auto;
        z-index: 9999;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    }
    .close-btn {
        position: absolute;
        top: 15px;
        right: 20px;
        background: #0969da;
        color: #fff;
        border: none;
        padding: 5px 12px;
        border-radius: 6px;
        cursor: pointer;
    }
    .close-btn:hover { background: #0860ca; }
    </style>
    """, unsafe_allow_html=True)

    # Background overlay
    st.markdown('<div class="modal-background"></div>', unsafe_allow_html=True)

    # Modal content
    st.markdown('<div class="modal-content">', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("❌ Close", key="popup_close"):
            st.session_state.show_popup = False
            st.session_state.edit_mode = False
            st.experimental_rerun()

        if st.button("✏️ Edit", key="popup_edit"):
            st.session_state.edit_mode = True

    with col1:
        # Always define points
        key_points = meeting.get('key_points', [])
        followup_points = meeting.get('followup_points', [])

        if st.session_state.edit_mode:
            title = st.text_input("Meeting Title", value=meeting.get('title', ''), key="popup_title")
            summary = st.text_area("Summary", value=meeting.get('summary', ''), height=100, key="popup_summary")

            st.write("**Key Points:**")
            updated_key_points = []
            for i, point in enumerate(key_points):
                p = st.text_input(f"Key Point {i+1}", value=point, key=f"popup_key_{i}")
                if p.strip(): updated_key_points.append(p)
            new_point = st.text_input("Add New Key Point", key="popup_new_key")
            if new_point.strip(): updated_key_points.append(new_point)

            st.write("**Follow-up Points:**")
            updated_followup = []
            for i, point in enumerate(followup_points):
                p = st.text_input(f"Follow-up Point {i+1}", value=point, key=f"popup_followup_{i}")
                if p.strip(): updated_followup.append(p)
            new_followup = st.text_input("Add New Follow-up", key="popup_new_followup")
            if new_followup.strip(): updated_followup.append(new_followup)

            next_schedule = st.date_input(
                "Next Meeting Schedule",
                value=pd.to_datetime(meeting.get('next_meet_schedule')).date() if meeting.get('next_meet_schedule') else None,
                key="popup_next_meeting"
            )

            if st.button("💾 Save Changes", key="popup_save"):
                success = update_meeting(
                    meeting['id'], title, summary, updated_key_points, updated_followup,
                    next_schedule.isoformat() if next_schedule else None
                )
                if success:
                    st.success("Meeting updated successfully!")
                    st.session_state.edit_mode = False
                    st.experimental_rerun()
                else:
                    st.error("Error updating meeting")
        else:
            # View mode
            st.markdown(f"**Title:** {meeting.get('title', 'N/A')}")
            source = "Automatic" if meeting.get('transcript_id') else "Manual"
            st.markdown(f"**Source:** {source}")
            st.markdown(f"**Created:** {pd.to_datetime(meeting['created_at']).strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Updated:** {pd.to_datetime(meeting['updated_at']).strftime('%Y-%m-%d %H:%M')}")
            st.markdown("**Summary:**")
            st.write(meeting.get('summary', 'No summary available'))

            st.markdown("**Key Points:**")
            if key_points:
                for i, point in enumerate(key_points, 1):
                    st.write(f"{i}. {point}")
            else:
                st.write("No key points available")

            st.markdown("**Follow-up Points:**")
            if followup_points:
                for i, point in enumerate(followup_points, 1):
                    st.write(f"{i}. {point}")
            else:
                st.write("No follow-up points available")

            if meeting.get('next_meet_schedule'):
                st.markdown(f"**Next Meeting:** {pd.to_datetime(meeting['next_meet_schedule']).strftime('%Y-%m-%d')}")

    st.markdown('</div>', unsafe_allow_html=True)

def manual_entry_form():
    with st.container():
        st.markdown('<div class="popup-container">', unsafe_allow_html=True)
        st.markdown("### ✏️ Manual Meeting Entry")
        
        with st.form("manual_entry_form"):
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
            
            submitted = st.form_submit_button("💾 Save Meeting")
            
            if submitted:
                if title and summary:
                    key_points = [point for point in [key_point_1, key_point_2, key_point_3] if point.strip()]
                    followup_points = [point for point in [followup_1, followup_2] if point.strip()]
                    next_schedule = next_meeting_date.isoformat() if next_meeting_date else None
                    
                    success = create_new_meeting(title, summary, key_points, followup_points, next_schedule)
                    
                    if success:
                        st.success("Meeting saved successfully!")
                        st.session_state.show_manual_entry = False
                        st.rerun()
                    else:
                        st.error("Error saving meeting. Please try again.")
                else:
                    st.error("Please fill in the required fields (Title and Summary)")
        
        st.markdown('</div>', unsafe_allow_html=True)

def meeting_details_tab():
    st.markdown('<div class="controls-section">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search meetings", placeholder="Search by title or content...")
    
    with col2:
        date_filter = st.selectbox("📅 Filter by Date", ["All", "Today", "This Week", "This Month", "Custom Range"])
    
    with col3:
        if st.button("➕ Manual Entry", key="manual_entry_btn"):
            st.session_state.show_manual_entry = True
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle date filtering logic (same as before)
    start_date = None
    end_date = None
    
    if date_filter == "Today":
        start_date = datetime.now().date()
        end_date = start_date
    elif date_filter == "This Week":
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif date_filter == "This Month":
        today = datetime.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    elif date_filter == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
    
    if st.session_state.get('show_manual_entry', False):
        manual_entry_form()
        if st.button("❌ Cancel", key="cancel_manual_entry"):
            st.session_state.show_manual_entry = False
            st.rerun()
        return
    
    meetings = fetch_meetings()
    
    if not meetings:
        st.info("🎯 No meetings found. Use the Manual Entry button to add your first meeting.")
        return
    
    # Process unprocessed transcripts
    for meeting in meetings:
        if meeting.get('transcript_id') and not meeting.get('summary'):
            transcript = fetch_transcript_by_id(meeting['transcript_id'])
            if transcript:
                processed_data = process_transcript_for_meeting(transcript)
                if processed_data:
                    update_meeting(
                        meeting['id'],
                        processed_data['title'],
                        processed_data['summary'],
                        processed_data['key_points'],
                        processed_data['followup_points'],
                        processed_data['next_meet_schedule']
                    )
    
    meetings = fetch_meetings()
    filtered_meetings = meetings
    
    if search_query:
        filtered_meetings = [
            m for m in filtered_meetings 
            if search_query.lower() in m.get('title', '').lower() or 
               search_query.lower() in m.get('summary', '').lower()
        ]
    
    if start_date and end_date:
        filtered_meetings = [
            m for m in filtered_meetings
            if start_date <= pd.to_datetime(m['created_at']).date() <= end_date
        ]
    
    if not filtered_meetings:
        st.info("🔍 No meetings match your search criteria.")
        return
    
    st.markdown(f"### 🎯 Found {len(filtered_meetings)} meeting(s)")
    
    for index, meeting in enumerate(filtered_meetings):
        card_html = create_meeting_card(meeting, index)
        st.markdown(card_html, unsafe_allow_html=True)
        
        if st.button(f"👁️ View Details", key=f"view_meeting_{index}"):
            st.session_state.selected_meeting = meeting
            st.session_state.show_popup = True
            st.session_state.edit_mode = False
    
    if st.session_state.show_popup and st.session_state.selected_meeting:
        show_meeting_popup(st.session_state.selected_meeting)

def space_management_tab():
    st.markdown("## 💾 Space Management")
    
    stats = get_database_stats()
    
    st.markdown("### 📊 Storage Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📋 Total Meetings</div>
            <div class="metric-value">{stats['meetings_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎤 Total Transcripts</div>
            <div class="metric-value">{stats['transcripts_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💾 Storage Used</div>
            <div class="metric-value">{stats['total_size_mb']:.1f} MB</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        remaining_storage = max(1024 - stats['total_size_mb'], 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔓 Available Space</div>
            <div class="metric-value">{remaining_storage:.1f} MB</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📈 Storage Usage")
    progress_value = min(stats['total_size_mb'] / 1024, 1.0)
    st.progress(progress_value)
    st.markdown(f"**💾 {stats['total_size_mb']:.1f} MB of 1024 MB used ({progress_value*100:.1f}%)**")
    
    if progress_value > 0.8:
        st.warning("⚠️ Storage is getting full! Consider deleting old records to free up space.")
    elif progress_value > 0.9:
        st.error("🚨 Storage is critically full! Please delete some records immediately.")
    
    st.markdown("### 📊 Storage Breakdown")
    
    fig = go.Figure(data=[
        go.Bar(name='Meetings', x=['Storage'], y=[stats['meetings_size_mb']]),
        go.Bar(name='Transcripts', x=['Storage'], y=[stats['transcripts_size_mb']])
    ])
    fig.update_layout(
        barmode='stack',
        title="Storage Usage by Data Type",
        yaxis_title="Size (MB)",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 🗂️ Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="controls-section">', unsafe_allow_html=True)
        st.markdown("#### 🗑️ Delete Old Records")
        
        cutoff_date = st.date_input(
            "Delete records older than:",
            value=datetime.now().date() - timedelta(days=30)
        )
        
        if st.button("🗑️ Delete Old Records", key="delete_old_records"):
            if st.checkbox("I understand this action cannot be undone", key="confirm_delete"):
                deleted_count = delete_old_records(cutoff_date.isoformat())
                if deleted_count > 0:
                    st.success(f"Deleted {deleted_count} old records successfully!")
                    st.rerun()
                else:
                    st.info("No records found matching the criteria.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="controls-section">', unsafe_allow_html=True)
        st.markdown("#### 📥 Export Data")
        
        export_start_date = st.date_input("Export from:", value=datetime.now().date() - timedelta(days=30))
        export_end_date = st.date_input("Export to:", value=datetime.now().date())
        
        if st.button("📥 Export to Excel", key="export_data"):
            csv_data = export_meetings_csv(
                export_start_date.isoformat(),
                export_end_date.isoformat()
            )
            
            if csv_data:
                st.download_button(
                    label="💾 Download Excel File",
                    data=csv_data,
                    file_name=f"meetings_export_{export_start_date}_to_{export_end_date}.csv",
                    mime="text/csv",
                    key="download_csv"
                )
                st.success("Data exported successfully! Click the download button above.")
            else:
                st.info("No data found for the selected date range.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 📈 Recent Activity")
    
    meetings = fetch_meetings()
    if meetings:
        recent_meetings = meetings[:10]
        
        activity_data = []
        for meeting in recent_meetings:
            activity_data.append({
                'Date': pd.to_datetime(meeting['created_at']).date(),
                'Title': meeting.get('title', 'Untitled'),
                'Source': '🤖 Automatic' if meeting.get('transcript_id') else '✍️ Manual',
                'Size (est.)': f"{len(str(meeting.get('summary', ''))) + len(str(meeting.get('key_points', [])))} chars"
            })
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent activity to display.")

def main():
    # Force the blue gradient title
    st.markdown('<h1 class="main-title">🎯 Meeting Manager</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 Meeting Details", "💾 Space Management"])
    
    with tab1:
        meeting_details_tab()
    
    with tab2:
        space_management_tab()

if __name__ == "__main__":
    main()





