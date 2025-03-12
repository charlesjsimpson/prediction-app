import streamlit as st
import sys
from pathlib import Path

# Add the project root to the path to ensure imports work correctly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

def check_authentication():
    """
    Check if the user is authenticated.
    If not, redirect to the main page.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    # Check if authentication state exists
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # If not authenticated, show error and stop
    if not st.session_state.authenticated:
        st.error("Please log in to access this page")
        st.info("Redirecting to login page...")
        
        # Add a button to go to the main page
        if st.button("Go to Login Page"):
            # This will only work when clicked
            st.switch_page("streamlit.py")
        
        # Stop execution of the rest of the page
        st.stop()
        return False
    
    return True
