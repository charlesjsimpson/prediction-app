import streamlit as st
from datetime import datetime
import sys
import os
import pandas as pd
import plotly.express as px
import calendar

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
# Import chart utilities
from fetch_data.fetch_data_PU import price

# Define custom blue color scheme
BLUE_COLORS = {
    '2023': '#0d47a1',  # Dark blue
    '2024': '#1976d2',  # Medium blue
    '2025': '#42a5f5'   # Light blue
}

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
        
        # Charts section
        st.subheader("Monthly Performance Metrics")
        
        # Create a function to generate monthly revenue bar chart
        def create_monthly_revenue_chart(df, start_date, end_date, years_to_include=[2023, 2024, 2025], metric='revenue'):
            """Create a monthly revenue bar chart for the specified years and date range.
            
            Parameters:
            -----------
            df : pandas.DataFrame
                DataFrame with hotel data
            start_date : datetime
                Start date for filtering data
            end_date : datetime
                End date for filtering data
            years_to_include : list
                List of years to include in the chart
                
            Returns:
            --------
            plotly.graph_objects.Figure
                Plotly figure object
            """
            # Create a copy to avoid modifying the original
            data = df.copy()
            
            # Ensure date column is datetime
            data['day'] = pd.to_datetime(data['day'])
            
            # Filter data for the specified years
            data = data[data['year'].isin(years_to_include)]
            
            # For each year, filter data from January 1 to the end_date's month and day
            filtered_data = pd.DataFrame()
            
            for year in years_to_include:
                # Calculate the end date for this year (same month and day as end_date)
                year_end_date = datetime(year, end_date.month, end_date.day)
                year_start_date = datetime(year, start_date.month, start_date.day)
                
                # Filter data for this year from January 1 to the end date
                year_data = data[
                    (data['year'] == year) & 
                    (data['day'] >= year_start_date) & 
                    (data['day'] <= year_end_date)
                ]
                
                filtered_data = pd.concat([filtered_data, year_data])
            
            # Group by year and month
            monthly_data = filtered_data.groupby(['year', pd.Grouper(key='day', freq='M')]).agg({
                'ca_room': 'sum'
            }).reset_index()
            
            # Format month names and add a sortable month number
            monthly_data['month'] = monthly_data['day'].dt.month
            monthly_data['month_name'] = monthly_data['day'].dt.strftime('%b')
            
            # Sort by month to ensure correct order
            monthly_data = monthly_data.sort_values(['month', 'year'])
            
            # Create the bar chart
            fig = px.bar(
                monthly_data,
                x='month_name',
                y='ca_room',
                color=monthly_data['year'].astype(str),
                barmode='group',
                color_discrete_map=BLUE_COLORS,
                labels={
                    'ca_room': 'Total Revenue (€)',
                    'month_name': 'Month',
                    'year': 'Year'
                },
                title=f'Monthly Total Revenue (Jan 1 - {end_date.strftime("%b %d")})',
                category_orders={
                    'month_name': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                }
            )
            
            # Customize layout
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Total Revenue (€)',
                legend_title='Year',
                height=500
            )
            
            # Format y-axis to show currency with appropriate decimal places
            if metric == 'revenue':
                fig.update_yaxes(
                    tickprefix='€',
                    tickformat=',d'  # Format as integer with thousands separator
                )
            else:  # avg_price
                fig.update_yaxes(
                    tickprefix='€',
                    tickformat=',.2f'  # Format with 2 decimal places
                )
            
            # Format hover template to show values without decimal places
            fig.update_traces(
                hovertemplate='%{y:,d} €<extra></extra>'
            )
            
            return fig
        
        # Calculate years to include (current year and two previous years)
        years_to_include = [year, year-1, year-2]
        
        # Create three columns for the charts
        col1, col2, col3 = st.columns(3)
        
        # Display the monthly revenue chart in the first column
        with col1:
            # Create and display the chart
            revenue_chart = create_monthly_revenue_chart(
                df, 
                start_date=datetime(year, 1, 1),  # January 1st of current year
                end_date=last_realized_date,      # Last day with complete data
                years_to_include=years_to_include
            )
            
            # Add text labels to each bar individually
            for i in range(len(revenue_chart.data)):
                revenue_chart.data[i].text = revenue_chart.data[i].y.astype(int)
                revenue_chart.data[i].textposition = 'outside'
                revenue_chart.data[i].texttemplate = '%{text:,d}'
                revenue_chart.data[i].textfont = dict(size=10)
            
            st.plotly_chart(revenue_chart, use_container_width=True)
            
            # Add an explanation
            st.caption(f"Monthly Total Revenue comparison for {', '.join(map(str, years_to_include))} from January 1 to {last_realized_date.strftime('%B %d')}")
        
        # Create a function to generate monthly occupancy rate chart
        def create_monthly_occupancy_chart(df, start_date, end_date, years_to_include=[2023, 2024, 2025]):
            """Create a monthly occupancy rate bar chart for the specified years and date range.
            
            Parameters:
            -----------
            df : pandas.DataFrame
                DataFrame with hotel data
            start_date : datetime
                Start date for filtering data
            end_date : datetime
                End date for filtering data
            years_to_include : list
                List of years to include in the chart
                
            Returns:
            --------
            plotly.graph_objects.Figure
                Plotly figure object
            """
            # Create a copy to avoid modifying the original
            data = df.copy()
            
            # Ensure date column is datetime
            data['day'] = pd.to_datetime(data['day'])
            
            # Filter data for the specified years
            data = data[data['year'].isin(years_to_include)]
            
            # For each year, filter data from January 1 to the end_date's month and day
            monthly_occupancy_data = []
            
            for year in years_to_include:
                # Calculate the end date for this year (same month and day as end_date)
                year_end_date = datetime(year, end_date.month, end_date.day)
                year_start_date = datetime(year, start_date.month, start_date.day)
                
                # Get the total number of rooms (constant for all years)
                total_rooms = get_total_rooms()
                
                # Process each month
                current_date = year_start_date
                while current_date <= year_end_date:
                    month = current_date.month
                    month_name = current_date.strftime('%b')
                    
                    # Calculate the start and end of this month
                    month_start = datetime(year, month, 1)
                    if month == end_date.month and year == end_date.year:
                        # For the current month, use the end_date
                        month_end = end_date
                    else:
                        # Get the last day of the month
                        next_month = month + 1 if month < 12 else 1
                        next_month_year = year if month < 12 else year + 1
                        month_end = datetime(next_month_year, next_month, 1) - pd.Timedelta(days=1)
                    
                    # Filter data for this month
                    month_data = data[
                        (data['year'] == year) & 
                        (data['day'] >= month_start) & 
                        (data['day'] <= month_end)
                    ]
                    
                    # Calculate occupancy rate using exact calendar days
                    days_in_period = get_days_in_period(month_start, month_end)
                    total_rooms_in_period = days_in_period * total_rooms
                    rooms_sold = month_data['n_rooms'].sum()
                    
                    # Calculate occupancy rate using the formula: (Rooms Sold / (Calendar Days × Total Rooms)) × 100
                    occupancy_rate = (rooms_sold / total_rooms_in_period) * 100 if total_rooms_in_period > 0 else 0
                    
                    # Add to results
                    monthly_occupancy_data.append({
                        'year': year,
                        'month': month,
                        'month_name': month_name,
                        'occupancy_rate': occupancy_rate,
                        'rooms_sold': rooms_sold,
                        'total_rooms_in_period': total_rooms_in_period,
                        'days_in_period': days_in_period
                    })
                    
                    # Move to the next month
                    next_month = month + 1 if month < 12 else 1
                    next_month_year = year if month < 12 else year + 1
                    current_date = datetime(next_month_year, next_month, 1)
            
            # Convert to DataFrame
            monthly_df = pd.DataFrame(monthly_occupancy_data)
            
            # Sort by month to ensure correct order
            monthly_df = monthly_df.sort_values(['month', 'year'])
            
            # Create the bar chart
            fig = px.bar(
                monthly_df,
                x='month_name',
                y='occupancy_rate',
                color=monthly_df['year'].astype(str),
                barmode='group',
                color_discrete_map=BLUE_COLORS,
                labels={
                    'occupancy_rate': 'Occupancy Rate (%)',
                    'month_name': 'Month',
                    'year': 'Year'
                },
                title=f'Monthly Occupancy Rate (Jan 1 - {end_date.strftime("%b %d")})',
                category_orders={
                    'month_name': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                }
            )
            
            # Customize layout
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Occupancy Rate (%)',
                legend_title='Year',
                height=500
            )
            
            # Format y-axis to show percentage without decimal places
            fig.update_yaxes(
                ticksuffix='%',
                tickformat=',.0f'  # Format as integer with thousands separator
            )
            
            # Format hover template to show values with one decimal place
            fig.update_traces(
                hovertemplate='%{y:.1f}%<extra></extra>'
            )
            
            return fig
        
        # Display the monthly occupancy rate chart in the second column
        with col2:
            # Create and display the chart
            occupancy_chart = create_monthly_occupancy_chart(
                df, 
                start_date=datetime(year, 1, 1),  # January 1st of current year
                end_date=last_realized_date,      # Last day with complete data
                years_to_include=years_to_include
            )
            
            # Add text labels to each bar individually
            for i in range(len(occupancy_chart.data)):
                occupancy_chart.data[i].text = occupancy_chart.data[i].y.round(1)  # Round to 1 decimal place
                occupancy_chart.data[i].textposition = 'outside'
                occupancy_chart.data[i].texttemplate = '%{text:.1f}'  # Show one decimal place
                occupancy_chart.data[i].textfont = dict(size=10)
            
            st.plotly_chart(occupancy_chart, use_container_width=True)
            
            # Add an explanation
            st.caption(f"Monthly Occupancy Rate comparison for {', '.join(map(str, years_to_include))} from January 1 to {last_realized_date.strftime('%B %d')}")
        
        # Create a function to generate monthly ADR chart
        def create_monthly_adr_chart(df, start_date, end_date, years_to_include=[2023, 2024, 2025]):
            """Create a monthly Average Daily Rate (ADR) chart for the specified years and date range.
            
            Parameters:
            -----------
            df : pandas.DataFrame
                DataFrame with hotel data
            start_date : datetime
                Start date for filtering data
            end_date : datetime
                End date for filtering data
            years_to_include : list
                List of years to include in the chart
                
            Returns:
            --------
            plotly.graph_objects.Figure
                Plotly figure object
            """
            # Create a copy to avoid modifying the original
            data = df.copy()
            
            # Ensure date column is datetime
            data['day'] = pd.to_datetime(data['day'])
            
            # Filter data for the specified years
            data = data[data['year'].isin(years_to_include)]
            
            # For each year, filter data from January 1 to the end_date's month and day
            monthly_adr_data = []
            
            for year in years_to_include:
                # Calculate the end date for this year (same month and day as end_date)
                year_end_date = datetime(year, end_date.month, end_date.day)
                year_start_date = datetime(year, start_date.month, start_date.day)
                
                # Process each month
                current_date = year_start_date
                while current_date <= year_end_date:
                    month = current_date.month
                    month_name = current_date.strftime('%b')
                    
                    # Calculate the start and end of this month
                    month_start = datetime(year, month, 1)
                    if month == end_date.month and year == end_date.year:
                        # For the current month, use the end_date
                        month_end = end_date
                    else:
                        # Get the last day of the month
                        next_month = month + 1 if month < 12 else 1
                        next_month_year = year if month < 12 else year + 1
                        month_end = datetime(next_month_year, next_month, 1) - pd.Timedelta(days=1)
                    
                    # Filter data for this month
                    month_data = data[
                        (data['year'] == year) & 
                        (data['day'] >= month_start) & 
                        (data['day'] <= month_end)
                    ]
                    
                    # Calculate ADR: Total Revenue / Rooms Sold
                    total_revenue = month_data['ca_room'].sum()
                    rooms_sold = month_data['n_rooms'].sum()
                    adr = total_revenue / rooms_sold if rooms_sold > 0 else 0
                    
                    # Add to results
                    monthly_adr_data.append({
                        'year': year,
                        'month': month,
                        'month_name': month_name,
                        'adr': adr,
                        'total_revenue': total_revenue,
                        'rooms_sold': rooms_sold
                    })
                    
                    # Move to the next month
                    next_month = month + 1 if month < 12 else 1
                    next_month_year = year if month < 12 else year + 1
                    current_date = datetime(next_month_year, next_month, 1)
            
            # Convert to DataFrame
            monthly_df = pd.DataFrame(monthly_adr_data)
            
            # Sort by month to ensure correct order
            monthly_df = monthly_df.sort_values(['month', 'year'])
            
            # Create the bar chart
            fig = px.bar(
                monthly_df,
                x='month_name',
                y='adr',
                color=monthly_df['year'].astype(str),
                barmode='group',
                color_discrete_map=BLUE_COLORS,
                labels={
                    'adr': 'Average Daily Rate (€)',
                    'month_name': 'Month',
                    'year': 'Year'
                },
                title=f'Monthly Average Daily Rate (Jan 1 - {end_date.strftime("%b %d")})',
                category_orders={
                    'month_name': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                }
            )
            
            # Customize layout
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Average Daily Rate (€)',
                legend_title='Year',
                height=500
            )
            
            # Format y-axis to show currency with one decimal place
            fig.update_yaxes(
                tickprefix='€',
                tickformat=',.1f'  # Format with one decimal place and thousands separator
            )
            
            # Add text labels to each bar individually
            for i in range(len(fig.data)):
                fig.data[i].text = fig.data[i].y.round(1)  # Round to 1 decimal place
                fig.data[i].textposition = 'outside'
                fig.data[i].texttemplate = '%{text:.1f}'  # Show one decimal place
                fig.data[i].textfont = dict(size=10)
                fig.data[i].hovertemplate = '%{y:.1f} €<extra></extra>'
            
            return fig
        
        # Display the ADR chart in the third column
        with col3:
            # Create and display the chart
            adr_chart = create_monthly_adr_chart(
                df, 
                start_date=datetime(year, 1, 1),  # January 1st of current year
                end_date=last_realized_date,      # Last day with complete data
                years_to_include=years_to_include
            )
            
            st.plotly_chart(adr_chart, use_container_width=True)
            
            # Add an explanation
            st.caption(f"Monthly Average Daily Rate comparison for {', '.join(map(str, years_to_include))} from January 1 to {last_realized_date.strftime('%B %d')}")
        
        # Add a divider before the revenue breakdown section
        st.divider()
        
        # Monthly Revenue Breakdown by Type_Detail Section
        st.subheader("Monthly Revenue Breakdown by Type_Detail")
        
        # Create a function to generate monthly revenue breakdown chart by Type_Detail with year comparison
        def create_monthly_revenue_breakdown_chart(df, month_filter, compare_years=[2023, 2024, 2025], metric='revenue'):
            """Create a monthly revenue breakdown chart by Type_Detail for the specified year and month.
            
            Parameters:
            -----------
            df : pandas.DataFrame
                DataFrame with hotel data
            year_filter : int
                Year to include in the chart
            month_filter : int
                Month to include in the chart
                
            Returns:
            --------
            plotly.graph_objects.Figure
                Plotly figure object
            """
            # Create a copy to avoid modifying the original
            data = df.copy()
            
            # Ensure we're working with numeric values
            data['ca_room'] = pd.to_numeric(data['ca_room'], errors='coerce')
            data['n_rooms'] = pd.to_numeric(data['n_rooms'], errors='coerce')
            
            # Filter data for the specified years and month
            data = data[data['year'].isin(compare_years) & (data['month'] == month_filter)]
            
            # Group by Type_Detail and year (using 'type' column instead since type_detail doesn't exist)
            type_data = data.groupby(['type', 'year']).agg({
                'ca_room': 'sum',
                'n_rooms': 'sum'
            }).reset_index()
            
            # Calculate average price (revenue / rooms sold)
            type_data['avg_price'] = type_data.apply(
                lambda row: row['ca_room'] / row['n_rooms'] if row['n_rooms'] > 0 else 0, 
                axis=1
            )
            
            # Define the main categories to keep
            main_categories = ['INDIV PUBL INDIRECT', 'INDIV PUBL DIRECT', 'NEGOCIES', 'GROUPES']
            
            # Create a copy of the original data
            combined_type_data = type_data.copy()
            
            # Process each year separately to combine categories
            result_data = []
            
            for year in compare_years:
                # Filter data for the current year
                year_data = combined_type_data[combined_type_data['year'] == year]
                
                # Filter rows for categories not in main_categories
                other_cat_data = year_data[~year_data['type'].isin(main_categories)]
                
                # Keep the main categories
                main_cat_data = year_data[year_data['type'].isin(main_categories)]
                
                # Sum the revenue for other categories
                if not other_cat_data.empty:
                    other_cat_sum = other_cat_data['ca_room'].sum()
                    
                    # Add a new row for "Other"
                    other_row = pd.DataFrame({'type': ['Other'], 'year': [year], 'ca_room': [other_cat_sum]})
                    
                    # Combine main categories with the "Other" category
                    year_result = pd.concat([main_cat_data, other_row], ignore_index=True)
                else:
                    year_result = main_cat_data
                
                # Add to the result
                result_data.append(year_result)
            
            # Combine all years
            combined_type_data = pd.concat(result_data, ignore_index=True)
            
            # Determine which metric to use
            if metric == 'revenue':
                y_column = 'ca_room'
                y_label = 'Revenue (€)'
                title_prefix = 'Monthly Revenue'
                # Format text as integer with commas
                text_format = combined_type_data[y_column].apply(lambda x: f"{int(x):,d}")
            else:  # avg_price
                y_column = 'avg_price'
                y_label = 'Average Price (€)'
                title_prefix = 'Monthly Average Price'
                # Format text with 2 decimal places
                text_format = combined_type_data[y_column].apply(lambda x: f"{x:.2f}")
            
            # Create the bar chart using px.bar to match Monthly Performance Metrics style
            fig = px.bar(
                combined_type_data,
                x='type',
                y=y_column,
                color=combined_type_data['year'].astype(str),
                barmode='group',
                color_discrete_map=BLUE_COLORS,
                labels={
                    y_column: y_label,
                    'type': 'Revenue Type',
                    'year': 'Year'
                },
                title=f'{title_prefix} Comparison by Type ({calendar.month_name[month_filter]} 2023-2025)',
                text=text_format
            )
            
            # Customize layout
            fig.update_layout(
                xaxis_title='Revenue Type',
                yaxis_title=y_label,
                height=500,
                # Format y-axis to show currency format with appropriate decimal places
                yaxis=dict(
                    tickformat=',.2f' if metric == 'avg_price' else ',.0f',
                    tickprefix='€',
                    separatethousands=True
                ),
                # Improve legend
                legend=dict(
                    title="Year",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Format y-axis to show currency with appropriate decimal places
            if metric == 'revenue':
                fig.update_yaxes(
                    tickprefix='€',
                    tickformat=',d'  # Format as integer with thousands separator
                )
            else:  # avg_price
                fig.update_yaxes(
                    tickprefix='€',
                    tickformat=',.2f'  # Format with 2 decimal places
                )
            
            # Ensure text is displayed properly
            fig.update_traces(
                textposition='outside',
                textfont=dict(size=10)
            )
            
            return fig
        
        # Get the current month's data
        current_month = last_realized_date.month
        
        # Create two columns for the charts
        col1, col2 = st.columns(2)
        
        # Create the revenue chart comparing 2023, 2024, and 2025 for the current month
        revenue_comparison_chart = create_monthly_revenue_breakdown_chart(
            df, 
            month_filter=current_month,
            compare_years=[2023, 2024, 2025],
            metric='revenue'
        )
        
        # Create the average price chart
        avg_price_comparison_chart = create_monthly_revenue_breakdown_chart(
            df, 
            month_filter=current_month,
            compare_years=[2023, 2024, 2025],
            metric='avg_price'
        )
        
        # Display the revenue chart in the first column
        with col1:
            st.plotly_chart(revenue_comparison_chart, use_container_width=True)
            st.caption(f"Monthly Revenue by Type ({calendar.month_name[current_month]} 2023-2025)")
        
        # Display the average price chart in the second column
        with col2:
            st.plotly_chart(avg_price_comparison_chart, use_container_width=True)
            st.caption(f"Monthly Average Price by Type ({calendar.month_name[current_month]} 2023-2025)")
        
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
