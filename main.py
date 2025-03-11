import streamlit as st
import sys
import os

# Add the project root to the path to ensure imports work correctly
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the main app functionality
try:
    from app.main import run_app
    
    # Run the main application
    run_app()
    
except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.write("Please check the console for more details.")
    
    # Display the directory structure for debugging
    st.code(f"Current directory: {os.getcwd()}")
    st.code(f"Files in root directory: {os.listdir(root_dir)}")
    st.code(f"Files in app directory: {os.listdir(os.path.join(root_dir, 'app'))}")
