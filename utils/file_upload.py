import os
import pandas as pd
import streamlit as st
from pathlib import Path
import shutil
import datetime

def validate_pu_file(uploaded_file):
    """
    Validate that the uploaded file meets the requirements:
    - Must be an Excel file (.xlsx)
    - Must be named '2025_PU.xlsx'
    
    Returns:
        tuple: (is_valid, message)
    """
    # Check if file was uploaded
    if uploaded_file is None:
        return False, "No file uploaded."
    
    # Check file extension
    if not uploaded_file.name.endswith('.xlsx'):
        return False, "File must be an Excel file (.xlsx)."
    
    # Check file name
    if not uploaded_file.name.startswith('2025_PU'):
        return False, "File must be named '2025_PU.xlsx'."
    
    return True, "File is valid."

def save_uploaded_file(uploaded_file):
    """
    Save the uploaded file to the data directory
    
    Args:
        uploaded_file: The uploaded file from st.file_uploader
        
    Returns:
        tuple: (success, message, file_path)
    """
    # Create data directory if it doesn't exist
    project_root = Path(__file__).parent.parent
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d")
    filename = f"2025_{timestamp}_PU.xlsx"
    file_path = os.path.join(data_dir, filename)
    
    # Also save with the standard name for direct loading
    standard_file_path = os.path.join(data_dir, "2025_PU.xlsx")
    
    try:
        # Save the uploaded file with timestamp
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Also save with the standard name (overwrite if exists)
        shutil.copy(file_path, standard_file_path)
        
        # Add the file to the list of files to load in fetch_data_PU.py
        update_file_list(filename)
        
        return True, f"File saved successfully as {filename}", file_path
    except Exception as e:
        return False, f"Error saving file: {str(e)}", None

def update_file_list(new_filename):
    """
    Update the list of files in fetch_data_PU.py to include the new file
    
    Args:
        new_filename: The name of the newly uploaded file
    """
    try:
        project_root = Path(__file__).parent.parent
        fetch_data_path = os.path.join(project_root, 'fetch_data', 'fetch_data_PU.py')
        
        # Read the current file
        with open(fetch_data_path, 'r') as file:
            lines = file.readlines()
        
        # Find the line with file_names list
        for i, line in enumerate(lines):
            if line.strip().startswith('file_names = ['):
                # Check if the new filename is already in the list
                if new_filename not in line:
                    # Replace the line with an updated list including the new file
                    # First, extract the existing list
                    start_idx = line.find('[')
                    end_idx = line.find(']')
                    if start_idx != -1 and end_idx != -1:
                        existing_list = line[start_idx+1:end_idx].strip()
                        # Add the new file to the list
                        if existing_list:
                            new_list = existing_list + f', "{new_filename}"'
                        else:
                            new_list = f'"{new_filename}"'
                        # Replace the line
                        lines[i] = line[:start_idx+1] + new_list + line[end_idx:]
                break
        
        # Write the updated content back to the file
        with open(fetch_data_path, 'w') as file:
            file.writelines(lines)
            
    except Exception as e:
        st.error(f"Error updating file list: {str(e)}")
