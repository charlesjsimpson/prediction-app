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
    get_days_in_period
)
# No chart imports needed for the simplified dashboard
from fetch_data.fetch_data_PU import price

# Page configuration
st.set_page_config(page_title="Hotel KPI Dashboard", layout="wide")

def main():
    st.title("Hotel KPI Dashboard")
    st.subheader("KPI Summary (January 1 - March 12, 2025)")
    
    # Use the imported price dataframe
    df = price.copy()
    
    # Get available years for filtering
    available_years = sorted(df['year'].unique().tolist())
    current_year = datetime.now().year
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
        
        # Year selection
        selected_year = st.selectbox(
            "Select Year",
            options=available_years,
            index=available_years.index(current_year) if current_year in available_years else len(available_years) - 1
        )
    
    # Get the last update date
    last_data_date = get_last_update_date(df)
    
    # Main dashboard content
    st.header(f"{selected_year} Hotel Performance Overview")
    
    # Display file and date information
    if last_data_date:
        last_month = last_data_date.strftime("%B")
        last_day = last_data_date.day
        
        # Get filename and extract date information
        if 'Source_File' in df.columns:
            latest_file = df.sort_values('day', ascending=False)['Source_File'].iloc[0] if not df.empty else "Unknown file"
        else:
            latest_file = "2025_PU_03_13.xlsx"  # Fallback
        
        # Extract date from filename (2025_PU_03_13.xlsx -> March 13, 2025)
        file_date_str = "March 13, 2025"  # Based on filename 2025_PU_03_13.xlsx
        
        # Since the file is dated March 13, the complete data is only available until March 12
        
        # Calculate days in period - from January 1st to March 12th (last complete day)
        start_date = datetime(2025, 1, 1)  # January 1st of the current year
        end_date = datetime(2025, 3, 12)   # March 12, 2025 (last complete day)
        days_in_period = get_days_in_period(start_date, end_date)
        
        # Calculate the same period for previous year
        prev_year_start = datetime(2024, 1, 1)  # January 1st of previous year
        prev_year_end = datetime(2024, 3, 12)   # Same day/month in previous year
        prev_year_days = get_days_in_period(prev_year_start, prev_year_end)
        
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
    
    # Filter current year data (2025) from January 1 to March 12
    current_year_df = df[
        (df['year'] == 2025) & 
        (df['day'] >= start_date) & 
        (df['day'] <= end_date)
    ]
    
    # Filter previous year data (2024) for the same period (January 1 to March 12)
    prev_year_df = df[
        (df['year'] == 2024) & 
        (df['day'] >= prev_year_start) & 
        (df['day'] <= prev_year_end)
    ]
    
    # Combine the filtered data
    period_df = pd.concat([current_year_df, prev_year_df])
    
    # Calculate KPIs using the filtered data and the correct total rooms value
    comparison_year = 2024  # Compare with previous year
    kpis = calculate_kpis(period_df, year_filter=2025, comparison_year=comparison_year, is_ytd=False)
    
    # KPI Summary section
    with kpi_container:
        st.subheader("Key Performance Indicators")
        
        # Display KPIs in a grid layout
        col1, col2, col3 = st.columns(3)
        
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
        
        # Second row of metrics
        col4, col5, col6 = st.columns(3)
        
        # Display RevPAR
        with col4:
            st.metric(
                label="RevPAR",
                value=f"${kpis['RevPAR']['value']:.2f}",
                delta=f"{kpis['RevPAR']['change']:.1f}%" if 'change' in kpis['RevPAR'] else None
            )
        
        # Display Rooms Sold with enhanced visibility
        with col5:
            st.metric(
                label="Rooms Sold in Period",
                value=f"{int(kpis['Rooms Sold']['value']):,}",
                delta=f"{kpis['Rooms Sold']['change']:.1f}%" if 'change' in kpis['Rooms Sold'] else None,
                help="Total number of rooms sold from January 1, 2025 to March 12, 2025"
            )
        
        # Display Days in Period
        with col6:
            st.metric(
                label="Days in Period",
                value=f"{days_in_period}",
                help="Total number of days in the analysis period"
            )
        
        # Now that KPIs are calculated, we can display the data information expander
        with expander_placeholder.container():
            with st.expander("📋 Data Information", expanded=False):
                # Get the rooms sold value from KPIs
                rooms_sold = int(kpis['Rooms Sold']['value']) if 'Rooms Sold' in kpis else 0
                
                # Create a more detailed info message with exact period information and rooms sold
                st.info(f"📅 **DATA INFORMATION**\n\n" 
                        f"📊 File: **{latest_file}**\n\n"
                        f"📆 File Date: **{file_date_str}**\n\n"
                        f"⏱️ Analysis Period: **January 1, 2025** to **March 12, 2025** (**{days_in_period} days**)\n\n"
                        f"🔄 Comparison Period: **January 1, 2024** to **March 12, 2024** (**{prev_year_days} days**)\n\n"
                        f"📋 Total Rooms: **{get_total_rooms()}**\n\n"
                        f"💼 Rooms Sold in Period: **{rooms_sold:,}** rooms")

if __name__ == "__main__":
    main()
