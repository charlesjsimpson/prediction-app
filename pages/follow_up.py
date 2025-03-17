import streamlit as st
from datetime import datetime
import sys
import os
import pandas as pd

# Add the parent directory to the path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.hotel_metrics import (
    get_last_update_date,
    calculate_kpis,
    ensure_datetime,
    get_total_rooms,
    set_total_rooms,
    get_days_in_period,
    count_full_occupancy_days
)
# No chart imports needed for the simplified dashboard
from fetch_data.fetch_data_PU import price

# Page configuration
st.set_page_config(page_title="Hotel KPI Dashboard", layout="wide")

def main():
    st.title("Hotel KPI Dashboard")
    
    # This will be updated once we have the actual date range
    
    # Use the imported price dataframe
    df = price.copy()
    
    # Set the current year for analysis
    year = 2025  # Current year for analysis
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Dashboard Configuration")
        
        # Room configuration
        current_total_rooms = get_total_rooms()
        new_total_rooms = st.number_input(
            "Total Number of Rooms",
            min_value=1,
            max_value=1000,
            value=current_total_rooms,
            step=1,
            help="Set the total number of rooms in the hotel for occupancy calculations"
        )
        
        if new_total_rooms != current_total_rooms:
            set_total_rooms(new_total_rooms)
            st.success(f"Total rooms updated to {new_total_rooms}")
        
        st.divider()
    
    # Get the last update date
    last_data_date = get_last_update_date(df)
    
    # Main dashboard content
    st.header(f"{year} Hotel Performance Overview")
    
    # Display file and date information
    if last_data_date:
        last_month = last_data_date.strftime("%B")
        last_day = last_data_date.day
        
        # Year is already defined at the top of the function
        
        # Get filename and extract date information - find the latest file for 2025
        def extract_date_from_filename(filename):
            """Extract date components from filename in format YYYY_PU_MM_DD.xlsx"""
            try:
                parts = filename.split('_')
                if len(parts) >= 4:
                    year_part = int(parts[0])
                    month_part = int(parts[2])
                    day_part = int(parts[3].split('.')[0])
                    return year_part, month_part, day_part
                return None
            except (ValueError, IndexError):
                return None
        
        # Get all 2025 files from the dataframe
        files_2025 = df[df['year'] == 2025]['Source_File'].unique() if 'Source_File' in df.columns else []
        
        # Default values in case no valid files are found
        file_date = datetime(year, 3, 17)  # Default to March 17, 2025
        file_date_str = file_date.strftime("%B %d, %Y")
        latest_file = "2025_PU_03_17.xlsx"  # Fallback to the latest known file
        
        if len(files_2025) > 0:
            # Process each file to find the latest one
            latest_date = (0, 0, 0)  # (year, month, day)
            
            for filename in files_2025:
                date_parts = extract_date_from_filename(filename)
                if date_parts and (date_parts[0] > latest_date[0] or 
                                 (date_parts[0] == latest_date[0] and date_parts[1] > latest_date[1]) or
                                 (date_parts[0] == latest_date[0] and date_parts[1] == latest_date[1] and date_parts[2] > latest_date[2])):
                    latest_date = date_parts
                    latest_file = filename
            
            # If we found a valid file, update the date information
            if latest_date != (0, 0, 0):
                year_part, month_part, day_part = latest_date
                file_date = datetime(year_part, month_part, day_part)
                file_date_str = file_date.strftime("%B %d, %Y")
                
                # Update the year variable based on the file
                year = year_part
        
        # The file date indicates when the report was generated
        # The complete data is available until the day before the file date
        
        # Calculate days in period - from January 1st to the last complete day
        start_date = datetime(year, 1, 1)  # January 1st of the current year
        
        # Define the last day where data is realized (YTD cutoff)
        # This is the key variable that should be used throughout the script
        # The last day with complete data is the day before the file date
        last_realized_date = file_date - pd.Timedelta(days=1)  # Last day with complete data
        end_date = last_realized_date  # Use this variable for all date-related calculations
        days_in_period = get_days_in_period(start_date, end_date)
        
        # Calculate the same period for previous year
        prev_year = year - 1  # Previous year for comparison
        prev_year_start = datetime(prev_year, 1, 1)  # January 1st of previous year
        prev_year_end = datetime(prev_year, last_realized_date.month, last_realized_date.day)  # Same day/month in previous year
        prev_year_days = get_days_in_period(prev_year_start, prev_year_end)
        
        # Now that we have the date range, update the subheader with dynamic dates
        st.subheader(f"KPI Summary (January 1 - {last_realized_date.strftime('%B %d, %Y')})")
        
        # Move the expander after KPI calculation to avoid undefined variable errors
        # We'll store the expander content in a variable to display it later
        expander_placeholder = st.empty()
            

        
        st.caption(f"Dashboard refreshed: {current_time}")
    else:
        st.caption(f"Dashboard refreshed: {current_time}")
    
    # Create a container for KPI Summary
    kpi_container = st.container()
    
    # Prepare data for comparison - using exact calendar days for accurate occupancy calculation
    
    # Filter data for the specific period (January 1 to March 13, 2025)
    df = ensure_datetime(df)  # Ensure dates are in datetime format
    
    # Filter current year data using the dynamic year variable
    current_year_df = df[
        (df['year'] == year) & 
        (df['day'] >= start_date) & 
        (df['day'] <= end_date)
    ]
    
    # Filter previous year data for the same period
    prev_year_df = df[
        (df['year'] == prev_year) & 
        (df['day'] >= prev_year_start) & 
        (df['day'] <= prev_year_end)
    ]
    
    # Combine the filtered data
    period_df = pd.concat([current_year_df, prev_year_df])
    
    # Calculate KPIs using the filtered data and the correct total rooms value
    comparison_year = prev_year  # Compare with previous year
    kpis = calculate_kpis(period_df, year_filter=year, comparison_year=comparison_year, is_ytd=False)
    
    # Calculate number of days with 100% occupancy for current and previous year
    full_occupancy_days_current = count_full_occupancy_days(df, year=year, is_ytd=True, current_date=end_date)
    full_occupancy_days_prev = count_full_occupancy_days(df, year=prev_year, is_ytd=True, current_date=prev_year_end)
    
    # Calculate percentage change in full occupancy days
    if full_occupancy_days_prev > 0:
        full_occupancy_change = ((full_occupancy_days_current - full_occupancy_days_prev) / full_occupancy_days_prev) * 100
    else:
        full_occupancy_change = float('inf') if full_occupancy_days_current > 0 else 0
    
    # KPI Summary section
    with kpi_container:
        st.subheader(f"Key Performance Indicators {year} - YTD")
        
        # Display all KPIs in a single row
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        # Display Total Revenue
        with col1:
            st.metric(
                label="Total Revenue",
                value=f"${kpis['Total Revenue']['value']:,.2f}",
                delta=f"{kpis['Total Revenue']['change']:.1f}%" if 'change' in kpis['Total Revenue'] else None
            )
        
        # Display Occupancy Rate
        with col2:
            st.metric(
                label="Occupancy Rate",
                value=f"{kpis['Occupancy Rate']['value']:.1f}%",
                delta=f"{kpis['Occupancy Rate']['change']:.1f}%" if 'change' in kpis['Occupancy Rate'] else None
            )
        
        # Display Average Daily Rate
        with col3:
            st.metric(
                label="Average Daily Rate (ADR)",
                value=f"${kpis['Average Daily Rate']['value']:.2f}",
                delta=f"{kpis['Average Daily Rate']['change']:.1f}%" if 'change' in kpis['Average Daily Rate'] else None
            )
        
        # Display RevPAR
        with col4:
            st.metric(
                label="RevPAR",
                value=f"${kpis['RevPAR']['value']:.2f}",
                delta=f"{kpis['RevPAR']['change']:.1f}%" if 'change' in kpis['RevPAR'] else None
            )
        
        # Display Rooms Sold
        with col5:
            st.metric(
                label="Rooms Sold",
                value=f"{int(kpis['Rooms Sold']['value']):,}",
                delta=f"{kpis['Rooms Sold']['change']:.1f}%" if 'change' in kpis['Rooms Sold'] else None,
                help=f"Total number of rooms sold from January 1 to {last_realized_date.strftime('%B %d')}, {year}"
            )
            
        # Display 100% Occupancy Days
        with col6:
            # Format the delta with appropriate sign and color
            if full_occupancy_change == float('inf'):
                delta_text = "N/A (prev. year: 0)"
            else:
                delta_text = f"{full_occupancy_change:.1f}%"
                
            st.metric(
                label="100% Occupancy Days",
                value=f"{full_occupancy_days_current}",
                delta=delta_text,
                help=f"Days with 100% occupancy rate from January 1 to {last_realized_date.strftime('%B %d')}, {year} (vs. {full_occupancy_days_prev} days in {prev_year})"
            )
        
        # Add a divider after the KPI section for a new section
        st.divider()
        
        # Space for a new section that will be used later
        st.container()
        
        # Now that KPIs are calculated, we can display the data information expander
        with expander_placeholder.container():
            with st.expander("📋 Data Information", expanded=False):
                # Create a more detailed info message with exact period information
                st.info(f"📅 **DATA INFORMATION**\n\n" 
                        f"📊 File: **{latest_file}**\n\n"
                        f"📆 File Date: **{file_date_str}**\n\n"
                        f"⏱️ Analysis Period: **January 1, {year}** to **{last_realized_date.strftime('%B %d, %Y')}** (**{days_in_period} days**)\n\n"
                        f"🔄 Comparison Period: **January 1, {prev_year}** to **{prev_year_end.strftime('%B %d, %Y')}** (**{prev_year_days} days**)\n\n"
                        f"📋 Total Rooms: **{get_total_rooms()}**")

if __name__ == "__main__":
    main()
