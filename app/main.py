import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from models import DataManager
from ai_service import OpenAIService
import re

# Load environment variables
load_dotenv()

def markdown_to_clean_text(markdown_text):
    """Convert markdown text to clean, readable text"""
    if not markdown_text:
        return ""

    # Remove markdown formatting
    clean_text = markdown_text

    # Remove bold/italic markers
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)  # Bold
    clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)      # Italic

    # Convert checkboxes to simple bullets
    clean_text = re.sub(r'- \[ \] ', '• ', clean_text)        # Empty checkboxes
    clean_text = re.sub(r'- \[x\] ', '• ', clean_text)        # Checked checkboxes

    # Clean up numbered lists (keep the numbers)
    clean_text = re.sub(r'^(\d+)\. ', r'\1. ', clean_text, flags=re.MULTILINE)

    # Clean up bullet points
    clean_text = re.sub(r'^- ', '• ', clean_text, flags=re.MULTILINE)

    return clean_text.strip()

# Page configuration
st.set_page_config(
    page_title="MoM Agent - Minutes of Meeting Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .section-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 1rem 0 0.5rem 0;
        color: #333;
    }
    .meeting-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-left: 3px solid #1f77b4;
        background-color: #f8f9fa;
    }
    .copy-button {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    if 'ai_service' not in st.session_state:
        # Initialize OpenAI service with environment variables
        env_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        env_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if env_api_key and env_api_key != "your_openai_api_key_here":
            st.session_state.ai_service = OpenAIService(env_api_key, env_model)
        else:
            st.error("⚠️ OpenAI API key not configured in .env file")
            st.stop()
    
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    
    if 'selected_meeting' not in st.session_state:
        st.session_state.selected_meeting = None
    
    if 'current_mom' not in st.session_state:
        st.session_state.current_mom = ""

# Clean MoM-only setup - no email services needed


def sidebar_projects():
    """Render projects and meetings sidebar"""
    with st.sidebar:
        st.markdown("## 📁 Projects")
        
        # Create new project
        with st.expander("➕ Create New Project"):
            project_name = st.text_input("Project Name", key="new_project_name")
            if st.button("Create Project", key="create_project_btn"):
                if project_name.strip():
                    if st.session_state.data_manager.create_project(project_name.strip()):
                        st.success(f"Project '{project_name}' created!")
                        st.rerun()
                    else:
                        st.error("Project already exists!")
                else:
                    st.error("Please enter a project name")
        
        # List existing projects
        projects = st.session_state.data_manager.get_projects()
        
        if not projects:
            st.info("No projects yet. Create your first project above.")
            return
        
        for project in projects:
            with st.expander(f"📁 {project}", expanded=(project == st.session_state.selected_project)):
                # Project actions row
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"Select {project}", key=f"select_project_{project}"):
                        st.session_state.selected_project = project
                        st.session_state.selected_meeting = None
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_project_{project}", help="Delete Project"):
                        # Set confirmation state
                        st.session_state[f"confirm_delete_project_{project}"] = True
                        st.rerun()

                # Project deletion confirmation
                if st.session_state.get(f"confirm_delete_project_{project}", False):
                    st.warning(f"⚠️ Delete project '{project}' and ALL its meetings?")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("✅ Yes", key=f"confirm_yes_{project}", type="primary", use_container_width=True):
                            if st.session_state.data_manager.delete_project(project):
                                if st.session_state.selected_project == project:
                                    st.session_state.selected_project = None
                                    st.session_state.selected_meeting = None
                                st.success(f"Project '{project}' deleted!")
                                del st.session_state[f"confirm_delete_project_{project}"]
                                st.rerun()
                            else:
                                st.error("Failed to delete project")
                    with col3:
                        if st.button("❌ No", key=f"confirm_no_{project}", use_container_width=True):
                            del st.session_state[f"confirm_delete_project_{project}"]
                            st.rerun()

                # Only show project contents if not in delete confirmation mode
                if not st.session_state.get(f"confirm_delete_project_{project}", False):
                    # Create new meeting in project
                    meeting_title = st.text_input(f"New Meeting Title", key=f"meeting_title_{project}")
                    if st.button(f"➕ Add Meeting", key=f"add_meeting_{project}"):
                        if meeting_title.strip():
                            meeting_id = st.session_state.data_manager.create_meeting(project, meeting_title.strip())
                            st.success(f"Meeting created!")
                            st.session_state.selected_project = project
                            st.session_state.selected_meeting = meeting_id
                            st.rerun()
                        else:
                            st.error("Please enter a meeting title")

                    # List meetings in project
                    meetings = st.session_state.data_manager.get_project_meetings(project)
                    if meetings:
                        st.markdown("**Meetings:**")
                        for meeting in meetings:
                            # Meeting row with delete button
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                meeting_display = f"{meeting['title']} ({meeting['date']})"
                                if st.button(meeting_display, key=f"meeting_{project}_{meeting['id']}"):
                                    st.session_state.selected_project = project
                                    st.session_state.selected_meeting = meeting['id']
                                    st.rerun()
                            with col2:
                                if st.button("🗑️", key=f"delete_meeting_{project}_{meeting['id']}", help="Delete Meeting"):
                                    # Set confirmation state
                                    st.session_state[f"confirm_delete_meeting_{project}_{meeting['id']}"] = True
                                    st.rerun()

                            # Meeting deletion confirmation
                            if st.session_state.get(f"confirm_delete_meeting_{project}_{meeting['id']}", False):
                                st.warning(f"⚠️ Delete meeting '{meeting['title']}'?")
                                col1, col2, col3 = st.columns([1, 1, 1])
                                with col1:
                                    if st.button("✅ Yes", key=f"confirm_yes_meeting_{project}_{meeting['id']}", type="primary", use_container_width=True):
                                        if st.session_state.data_manager.delete_meeting(project, meeting['id']):
                                            if st.session_state.selected_meeting == meeting['id']:
                                                st.session_state.selected_meeting = None
                                            st.success(f"Meeting '{meeting['title']}' deleted!")
                                            del st.session_state[f"confirm_delete_meeting_{project}_{meeting['id']}"]
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete meeting")
                                with col3:
                                    if st.button("❌ No", key=f"confirm_no_meeting_{project}_{meeting['id']}", use_container_width=True):
                                        del st.session_state[f"confirm_delete_meeting_{project}_{meeting['id']}"]
                                        st.rerun()

def main_content():
    """Render main content area"""
    if not st.session_state.selected_project:
        st.markdown('<div class="main-header">📝 MoM Agent</div>', unsafe_allow_html=True)
        st.markdown("### Welcome to Minutes of Meeting Generator")
        st.info("👈 Select or create a project from the sidebar to get started.")
        return
    
    if not st.session_state.selected_meeting:
        st.markdown(f'<div class="main-header">📁 {st.session_state.selected_project}</div>', unsafe_allow_html=True)
        st.info("👈 Select or create a meeting from the sidebar to continue.")
        return
    
    # Load current meeting
    meeting_data = st.session_state.data_manager.get_meeting(
        st.session_state.selected_project, 
        st.session_state.selected_meeting
    )
    
    if not meeting_data:
        st.error("Meeting not found!")
        return
    
    st.markdown(f'<div class="main-header">{meeting_data["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f"**Project:** {st.session_state.selected_project} | **Date:** {meeting_data['date']}")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📝 Generate MoM", "✏️ Edit MoM", "📋 Final Draft"])
    
    with tab1:
        st.markdown('<div class="section-header">Meeting Transcript</div>', unsafe_allow_html=True)

        # Transcript input
        transcript = st.text_area(
            "Paste your meeting transcript here:",
            value=meeting_data.get('transcript', ''),
            height=250,
            placeholder="Paste the meeting transcript here..."
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 Save Transcript", type="secondary"):
                meeting_data['transcript'] = transcript
                st.session_state.data_manager.save_meeting(st.session_state.selected_project, meeting_data)
                st.success("Transcript saved!")
        
        with col2:
            if st.button("🤖 Generate MoM", type="primary", disabled=not transcript.strip()):
                if transcript.strip():
                    with st.spinner("Generating Minutes of Meeting..."):
                        # Get project context
                        context = st.session_state.data_manager.get_project_context(st.session_state.selected_project)
                        
                        # Generate MoM
                        generated_mom = st.session_state.ai_service.generate_mom(
                            transcript, 
                            context, 
                            st.session_state.selected_project
                        )
                        
                        if generated_mom:
                            meeting_data['transcript'] = transcript
                            meeting_data['draft_mom'] = generated_mom
                            st.session_state.data_manager.save_meeting(st.session_state.selected_project, meeting_data)
                            st.session_state.current_mom = generated_mom
                            st.success("✅ MoM generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate MoM. Please try again.")
        
        # Show generated MoM if exists
        if meeting_data.get('draft_mom'):
            st.markdown('<div class="section-header">Generated MoM (Draft)</div>', unsafe_allow_html=True)
            st.markdown(meeting_data['draft_mom'])
    
    with tab2:
        st.markdown('<div class="section-header">Edit Minutes of Meeting</div>', unsafe_allow_html=True)
        
        if not meeting_data.get('draft_mom'):
            st.info("Generate a MoM first in the 'Generate MoM' tab.")
            return
        
        # Editable MoM
        edited_mom = st.text_area(
            "Edit the generated MoM:",
            value=meeting_data.get('final_mom') or meeting_data.get('draft_mom', ''),
            height=400
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 Save Changes", type="secondary"):
                meeting_data['final_mom'] = edited_mom
                st.session_state.data_manager.save_meeting(st.session_state.selected_project, meeting_data)
                st.success("Changes saved!")
        
        with col2:
            if st.button("📋 Copy to Clipboard", type="primary"):
                # Convert markdown to clean text and display
                clean_text = markdown_to_clean_text(edited_mom)
                st.success("📋 Clean MoM ready to copy - use the copy button in the text block below:")
                st.code(clean_text, language="text")
    
    with tab3:
        st.markdown('<div class="section-header">Final Minutes of Meeting</div>', unsafe_allow_html=True)
        
        final_mom = meeting_data.get('final_mom') or meeting_data.get('draft_mom')
        
        if final_mom:
            st.markdown(final_mom)
            
            # Copy button
            if st.button("📋 Copy Final MoM", type="primary", key="copy_final"):
                # Convert markdown to clean text and display
                clean_text = markdown_to_clean_text(final_mom)
                st.success("📋 Clean Final MoM ready to copy - use the copy button in the text block below:")
                st.code(clean_text, language="text")

        else:
            st.info("No MoM generated yet. Go to 'Generate MoM' tab to create one.")

def main():
    """Main application function"""
    init_session_state()
    
    # Render sidebar with projects
    sidebar_projects()
    
    # Render main content
    main_content()

if __name__ == "__main__":
    main()