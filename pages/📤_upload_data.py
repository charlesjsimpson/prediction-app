import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import datetime

# Add the project root to the path to ensure imports work correctly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Import the authentication protection
from utils.page_protection import check_authentication
from utils.file_upload import validate_pu_file, save_uploaded_file
from fetch_data.fetch_data_PU import load_data

# Check if user is authenticated before proceeding
if not check_authentication():
    # If not authenticated, the check_authentication function will stop execution
    st.stop()

# Set page title and header
st.title("Upload Financial Data")
st.header("Update Hotel Financial Data")

# Add description and instructions
st.markdown("""
This page allows you to upload the latest financial data for your hotel. 
The uploaded file will be used to update the dashboard and financial reports.

### Requirements:
- File must be an Excel file (.xlsx)
- File must be named '2025_PU.xlsx'
- Data should be in the standard format with the first row as headers
""")

# Create a file uploader widget
uploaded_file = st.file_uploader("Upload 2025_PU.xlsx file", type=["xlsx"])

# Add validation and processing when a file is uploaded
if uploaded_file is not None:
    # Validate the file
    is_valid, validation_message = validate_pu_file(uploaded_file)
    
    if not is_valid:
        st.error(validation_message)
    else:
        # Show file details
        st.success(validation_message)
        st.info(f"File name: {uploaded_file.name}")
        st.info(f"File size: {uploaded_file.size} bytes")
        
        # Add a button to process the file
        if st.button("Process and Update Financial Data"):
            # Save the file
            success, message, file_path = save_uploaded_file(uploaded_file)
            
            if success:
                st.success(message)
                
                # Preview the data
                try:
                    # Load the data from the uploaded file
                    df = pd.read_excel(uploaded_file, sheet_name=0, skiprows=1, engine="openpyxl")
                    
                    # Display a sample of the data
                    st.subheader("Data Preview")
                    st.dataframe(df.head(10))
                    
                    # Show some statistics
                    st.subheader("Data Statistics")
                    st.write(f"Number of rows: {df.shape[0]}")
                    st.write(f"Number of columns: {df.shape[1]}")
                    
                    # Reload the data to update the dashboard
                    st.info("Reloading data for the dashboard...")
                    price, df_1 = load_data()
                    
                    st.success(f"Financial data successfully updated with {price.shape[0]} records!")
                    
                    # Add a button to go to the analysis page
                    if st.button("View Updated Dashboard"):
                        st.switch_page("pages/📈_analysis.py")
                    
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
            else:
                st.error(message)
else:
    st.info("Please upload a file to proceed.")

# Add a section with additional information
st.markdown("---")
st.subheader("Data Update History")

# Try to list previously uploaded files
try:
    data_dir = os.path.join(root_dir, 'data')
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('_PU.xlsx')]
        files.sort(reverse=True)  # Show newest files first
        
        if files:
            st.write("Previously uploaded files:")
            for file in files:
                file_path = os.path.join(data_dir, file)
                file_stats = os.stat(file_path)
                file_size = file_stats.st_size / 1024  # Convert to KB
                modified_time = datetime.datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                st.write(f"- **{file}** (Size: {file_size:.2f} KB, Last modified: {modified_time})")
        else:
            st.write("No previous uploads found.")
    else:
        st.write("Data directory not found.")
except Exception as e:
    st.error(f"Error listing files: {str(e)}")
