import streamlit as st
import sys
import os

# Add the project root to the path to ensure imports work correctly
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    
# Import the new cloud-friendly authentication system
from utils.cloud_auth import login_form

# Set page configuration
st.set_page_config(
    page_title="Hotel Financial Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Handle authentication
if login_form():
    # User is authenticated, show the dashboard
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    
    # Import the main app functionality
    try:
        # First try the standard import path
        from app.main import run_app
        run_app()
    except ImportError as e:
        st.error(f"Import error: {e}")
        st.info("Trying alternative import paths...")
        
        try:
            # Try adding app directory to path
            app_path = os.path.join(root_dir, 'app')
            if app_path not in sys.path:
                sys.path.append(app_path)
            
            # Try direct import
            from main import run_app
            run_app()
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")
            
            # Display debugging information
            st.subheader("Debugging Information")
            st.code(f"Current directory: {os.getcwd()}")
            st.code(f"Python path: {sys.path}")
            st.code(f"Files in root directory: {os.listdir(root_dir)}")
            
            if os.path.exists(os.path.join(root_dir, 'app')):
                st.code(f"Files in app directory: {os.listdir(os.path.join(root_dir, 'app'))}")
            
            # Fallback to a simple interface
            st.warning("Falling back to simple interface due to import errors.")
            st.info("Please check the logs for more information on how to fix this issue.")
