import streamlit as st
import sys
import os
from utils.logging_system import setup_logger, log_action, log_page_access, log_error
from utils.cloud_auth import login_form

# Add the project root to the path to ensure imports work correctly
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Set up the main application logger
main_logger = setup_logger('hotel_dashboard_main')
main_logger.info("Starting Hotel Financial Dashboard application")

# Set page configuration
st.set_page_config(
    page_title="Hotel Financial Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Handle authentication
try:
    if login_form():
        # User is authenticated, show the dashboard
        st.sidebar.title(f"Welcome, {st.session_state.username}!")
        log_action("User authenticated", user=st.session_state.username)
        log_page_access("Main Dashboard")
except Exception as e:
    error_msg = f"Authentication error: {e}"
    log_error(error_msg, e)
    st.error(error_msg)
    
    # Import the main app functionality
    try:
        # First try the standard import path
        log_action("Loading main application")
        from app.main import run_app
        run_app()
        log_action("Application loaded successfully")
    except ImportError as e:
        error_msg = f"Import error: {e}"
        log_error(error_msg, e)
        st.error(error_msg)
        st.info("Trying alternative import paths...")
        
        try:
            # Try adding app directory to path
            app_path = os.path.join(root_dir, 'app')
            if app_path not in sys.path:
                sys.path.append(app_path)
            
            # Try direct import
            log_action("Attempting alternative import path")
            from main import run_app
            run_app()
            log_action("Application loaded successfully via alternative path")
        except Exception as e:
            error_msg = f"Error loading dashboard: {e}"
            log_error(error_msg, e)
            st.error(error_msg)
            
            # Display debugging information
            st.subheader("Debugging Information")
            debug_info = {
                "Current directory": os.getcwd(),
                "Python path": sys.path,
                "Files in root directory": os.listdir(root_dir)
            }
            log_action("Displaying debugging information", details=str(debug_info))
            st.code(f"Current directory: {os.getcwd()}")
            st.code(f"Python path: {sys.path}")
            st.code(f"Files in root directory: {os.listdir(root_dir)}")
            
            if os.path.exists(os.path.join(root_dir, 'app')):
                st.code(f"Files in app directory: {os.listdir(os.path.join(root_dir, 'app'))}")
            
            # Fallback to a simple interface
            st.warning("Falling back to simple interface due to import errors.")
            st.info("Please check the logs for more information on how to fix this issue.")
