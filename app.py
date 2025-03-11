import os
import sys

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# This file serves as an entry point for running the Streamlit app
if __name__ == "__main__":
    # Import and run the main module when script is run directly
    from app.main import *  # noqa: F403
