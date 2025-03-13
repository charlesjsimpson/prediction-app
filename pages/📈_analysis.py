import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
from utils.page_protection import check_authentication
from utils.logging_system import log_page_access, log_data_operation, log_error, log_action
from fetch_data.fetch_data_PU import load_data
from utils.analysis import calculate_metrics, plot_revenue_trend, plot_occupancy_by_day_of_week, forecast_revenue, plot_revenue_by_type, compare_years

# Add the project root to the path to ensure imports work correctly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Check if user is authenticated before proceeding
if not check_authentication():
    # If not authenticated, the check_authentication function will stop execution
    log_action("Authentication failed", level="warning")
    st.stop()

# Log page access
log_page_access("Analysis Dashboard")

# Suppress warnings
warnings.filterwarnings('ignore')

# Load the data
try:
    log_data_operation("loading", "price data")
    price, df_1 = load_data()
    
    # Combine the dataframes if df_1 is not empty
    if not df_1.empty:
        price = pd.concat([price, df_1], ignore_index=True)
        log_data_operation("combining", "price data", "Combined multiple dataframes")
        
    # Ensure that the 'day' column is correctly set up
    price['day'] = pd.to_datetime(price['day'], errors='coerce')
    
    # Create formatted columns without losing the datetime object
    price['formatted_day'] = price['day'].dt.strftime('%A, %B %d').str.replace(' 0', ' ')  # Format as 'Wednesday, January 1'
    price['month'] = price['day'].dt.strftime('%B')  # Format month as 'January'
    price['year'] = price['day'].dt.year  # Keep year as a separate column
    
    # Get week number
    price['week'] = price['day'].dt.isocalendar().week
    
    log_data_operation("processed", "price data", f"Successfully processed {len(price)} records")
    st.success(f"Data loaded successfully! {len(price)} records found.")
except Exception as e:
    error_msg = f"Error loading or processing data: {e}"
    log_error(error_msg, e)
    st.error(error_msg)
    price = pd.DataFrame()
    # Show detailed error information in an expander
    with st.expander("Error Details"):
        st.code(str(e))
        
        # Check if data files exist
        data_dir = os.path.join(root_dir, 'data')
        st.write(f"Checking data directory: {data_dir}")
        log_data_operation("checking", "data directory", f"Checking {data_dir}")
        
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            st.write(f"Files found: {', '.join(files)}")
            log_data_operation("found", "data files", f"Found {len(files)} files")
        else:
            st.write("Data directory not found!")
            log_error("Data directory not found", None)
    st.stop()

# Set the title of the page
st.title("Pricing Analysis")

# Add space between the two tabs
st.write("")

# Change the order of the tabs
tabs = ['Monthly_recap', 'Y-Y_recap', 'Daily', 'Daily_y_Y', 'Summary']

# Create tabs in the Streamlit app
tab_monthly_recap, tab_y_y_recap, tab_daily, tab_daily_y_y, _ = st.tabs(tabs)

# Ensure that the 'day' column is correctly set up
price['day'] = pd.to_datetime(price['day'], format='%d-%m-%Y', errors='coerce')

# Create formatted columns without losing the datetime object
price['formatted_day'] = price['day'].dt.strftime('%A, %B %d').str.replace(' 0', ' ')  # Format as 'Wednesday, January 1'
price['month'] = price['day'].dt.strftime('%B')  # Format month as 'January'
price['year'] = price['day'].dt.year  # Keep year as a separate column

# Get week number
price['week'] = price['day'].dt.isocalendar().week  

vacation_periods = [
    ('2025-01-01', '2025-01-06'),
    ('2025-02-15', '2025-03-03'),
    ('2025-04-21', '2025-04-28'),
    ('2025-07-05', '2025-09-01'),
    ('2025-10-20', '2025-10-31'),
    ('2025-12-22', '2025-12-31')
]

# Define French public holidays in 2025
public_holidays = [
    '2025-01-01',  # New Year's Day
    '2025-04-21',  # Easter Monday
    '2025-05-01',  # Labour Day
    '2025-05-08',  # Victory Day
    '2025-05-29',  # Ascension Day
    '2025-06-09',  # Whit Monday
    '2025-07-14',  # Bastille Day
    '2025-11-01',  # All Saints' Day
    '2025-11-11',  # Armistice Day
    '2025-12-25',  # Christmas Day,
]

special_events = [
    ('2025-02-22', '2025-03-02', "Salon de l'agriculture", 18),  
    ('2025-05-25', '2025-06-08', "Rolland Garros", 30),  
    ('2025-06-15', '2025-06-23', "AIRSHOW", 110),  
    ('2025-11-16', '2025-11-21', "Congrès des Maires", 60),  
    ('2025-01-30', '2025-01-30', "veille de match", 20),  
    ('2025-03-14', '2025-03-14', "veille de match", 20),  
    ('2025-10-14', '2025-10-18', "equip auto", 60),  
    ('2025-10-29', '2025-11-02', "salon chocolat", 20),  
    ('2025-11-04', '2025-11-06', "salon nucléaire", 50)    
]


# Define the month order
month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Order the DataFrame by year and month
price['month'] = pd.Categorical(price['month'], categories=month_order, ordered=True)
price = price.sort_values(by=['year', 'month'])

# Define the mapping for categories
category_mapping = {
    'INDIV PUBL DIRECT': 'INDIV D',
    'INDIV PUBL INDIRECT': 'INDIV I',
    'NEGOCIES': 'NEGOCIES',
    'GROUPES': 'GROUPES',
    'B': 'OTHER',
    'AUTRE': 'OTHER',
    '** Type Non défini': 'OTHER'  
}

# Apply the mapping to the 'type' column
if 'type' in price.columns:
    price['type'] = price['type'].replace(category_mapping)

# Check which tab is selected and display content accordingly
with tab_monthly_recap:
    st.title('Monthly Recap')
    # Add select boxes for period and year
    years = sorted(price['year'].unique())
    default_index = min(len(years) - 1, 0)  # Default to the last year or 0 if empty
    selected_year = st.selectbox('Select Year:', years, index=default_index)
    period = st.selectbox('Select Period for Analysis:', ['Monthly', 'Weekly'], index=0)

    # Filter the price DataFrame by the selected year
    filtered_price = price[price['year'] == selected_year]

    # Create a pivot table based on the selected period
    if period == 'Monthly':
        price_type = filtered_price.pivot_table(index='month', columns='type', values=['n_rooms', 'ca_room'], aggfunc='sum', fill_value=0)
    elif period == 'Weekly':
        price_type = filtered_price.pivot_table(index='week', columns='type', values=['n_rooms', 'ca_room'], aggfunc='sum', fill_value=0)

    # Format the CA_room values to show no figures after the decimal point
    price_type['ca_room'] = price_type['ca_room'].astype(int)

    # Add total row for n_rooms and ca_room
    price_type.loc['Total'] = price_type.sum(numeric_only=True)

    # Separate total rooms and total CA rooms into distinct columns
    price_type['Total Rooms'] = (
        price_type[('n_rooms', 'GROUPES')] + 
        price_type[('n_rooms', 'INDIV I')] + 
        price_type[('n_rooms', 'INDIV D')] + 
        price_type[('n_rooms', 'NEGOCIES')] +
        price_type[('n_rooms', 'OTHER')] 
    )

    price_type['Total CA Rooms'] = (
        price_type[('ca_room', 'GROUPES')] + 
        price_type[('ca_room', 'INDIV I')] + 
        price_type[('ca_room', 'INDIV D')] + 
        price_type[('ca_room', 'NEGOCIES')] +
        price_type[('ca_room', 'OTHER')]
    )

    # Calculate PM and OR columns
    if period == 'Monthly':
        # Get the number of days in the selected month
        month_days = filtered_price['day'].dt.days_in_month.unique()[0]  
        price_type['PM'] = (price_type['Total CA Rooms'] / price_type['Total Rooms']).fillna(0) 
        price_type['OR'] = price_type['Total Rooms'] / (70 * month_days)  
    elif period == 'Weekly':
        price_type['PM'] = (price_type['Total CA Rooms'] / price_type['Total Rooms']).fillna(0)   
        price_type['OR'] = price_type['Total Rooms'] / (70 * 7)

    # Format PM and OR columns
    price_type['PM'] = price_type['PM'].round(0).astype(int)  
    price_type['OR'] = (price_type['OR'] * 100).round(1)  

    # Drop the 'OTHER' columns
    price_type = price_type.drop(columns=[('n_rooms', 'OTHER'), ('ca_room', 'OTHER')], errors='ignore')

    # Merge the second row with the type into a single row
    price_type.columns = [f'{col[1]} - {col[0]}' for col in price_type.columns]

    # Display the pivot table results
    st.write(f"{period} pivot table for each category:")
    st.write(price_type)

with tab_y_y_recap:
    st.title('Year-over-Year Recap')

    # Create a mapping for categories
    category_mapping = {
        'GROUPES': 'GROUPES',
        'B': 'OTHER',
        'AUTRE': 'OTHER',
        '** Type Non défini': 'OTHER'
    }

    # Group the price DataFrame by type using the category mapping
    grouped_data = price.copy()
    grouped_data['type'] = grouped_data['type'].replace(category_mapping)  # Apply mapping

    # Get the current month
    today = datetime.now()
    current_month = today.month

    # Select month for comparison with default values
    selected_month = st.selectbox('Select Month:', ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], index=current_month - 1)

    # Prepare DataFrames for available years
    y_y_dataframes = {}
    available_years = sorted(grouped_data['year'].unique())
    for year in available_years:
        filtered_data = grouped_data[grouped_data['year'] == year]
        filtered_data = filtered_data[filtered_data['month'] == selected_month]  # Filter by selected month
        y_y_dataframes[year] = filtered_data.groupby('type').agg({'n_rooms': 'sum', 'ca_room': 'sum'}).reset_index()

        # Add a sum row to each DataFrame
        sum_row = y_y_dataframes[year].sum(numeric_only=True)
        sum_row['type'] = 'Total'
        y_y_dataframes[year] = pd.concat([y_y_dataframes[year], sum_row.to_frame().T], ignore_index=True)

        # Calculate PM and add it as a new column
        y_y_dataframes[year]['PM'] = (y_y_dataframes[year]['ca_room'] / y_y_dataframes[year]['n_rooms']).fillna(0) 
        y_y_dataframes[year]['PM'] = y_y_dataframes[year]['PM'].astype(int)  # No figures after the decimal point

    # Format 'ca_room' values to show no figures after the decimal point
    for year in y_y_dataframes:
        y_y_dataframes[year]['ca_room'] = y_y_dataframes[year]['ca_room'].astype(int)

    # Display the comparison results side by side
    st.subheader('Comparison Results')
    cols = st.columns(3)  # Create 3 columns for the 3 years
    for i, (year, data) in enumerate(y_y_dataframes.items()):
        with cols[i]:
            st.write(f'Data for {year}:')
            st.write(data)

with tab_daily:
    st.title('Daily Room Details')

    # Create a mapping for categories
    category_mapping = {
        'GROUPES': 'GROUPES',
        'B': 'OTHER',
        'AUTRE': 'OTHER',
        '** Type Non défini': 'OTHER'
    }

    # Group the price DataFrame by type using the category mapping
    grouped_data = price.copy()
    grouped_data['type'] = grouped_data['type'].replace(category_mapping)  # Apply mapping

    # Convert 'day' column to datetime format
    grouped_data['day'] = pd.to_datetime(grouped_data['day'], format='%A %B %d', errors='coerce')

    # Filter data for the next 30 days
    today = datetime.now()
    next_30_days = pd.date_range(start=today, periods=30).date

    # Prepare DataFrame for the next 30 days
    daily_data = grouped_data[grouped_data['day'].dt.date.isin(next_30_days)]

    # Pivot the DataFrame to have a column for each type
    daily_summary = daily_data.pivot_table(index='day', columns='type', values=['n_rooms', 'ca_room'], aggfunc='sum').fillna(0)

    # Combine column names to make them unique and remove 'room'
    daily_summary.columns = [f'{value}_{key}'.replace('rooms', '').replace('room', '') for key, value in daily_summary.columns]

    # Format the 'day' column to display as 'Monday January 12'
    daily_summary.index = daily_summary.index.strftime('%A %B %d')

    # Format 'ca_room' values to show no figures after the decimal point
    daily_summary = daily_summary.astype(int)

    # Calculate total rooms and total CA rooms
    daily_summary['Total_n'] = daily_summary.filter(like='n_').sum(axis=1)
    daily_summary['Total_ca'] = daily_summary.filter(like='ca_').sum(axis=1)

    # Calculate PM (Performance Metric) and OR (Occupancy Rate)
    daily_summary['PM'] = (daily_summary['Total_ca'] / daily_summary['Total_n']).fillna(0) 
    daily_summary['OR'] = (daily_summary['Total_n'] / 70).fillna(0) * 100

    # Format PM to show one decimal place
    daily_summary['PM'] = daily_summary['PM'].round(1)  # One decimal place
    daily_summary['OR'] = daily_summary['OR'].astype(int)  # Format OR to show no figures after the decimal point

    # Display the daily summary
    st.subheader('Room Details for the Next 30 Days')
    st.write(daily_summary)

with tab_daily_y_y:
    st.title('Daily View')

    # Get today's date
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create date range starting from today for the next 30 days
    date_range = pd.date_range(start=today, periods=30)

    # Filter data for the next 30 days
    filtered_data = price[price['day'].dt.normalize().isin(date_range)]

    # Group by day and calculate totals for 2025
    daily_summary = filtered_data.groupby('day').agg({
        'n_rooms': 'sum',
        'ca_room': 'sum'
    }).reset_index()

    # Make sure we have all dates in the range (even if no data)
    all_dates = pd.DataFrame({'day': date_range})
    daily_summary = pd.merge(all_dates, daily_summary, on='day', how='left')
    daily_summary = daily_summary.fillna(0)

    # Function to get the same day of week from previous year
    def get_same_day_previous_year(date):
        # Get the same weekday from previous year
        days_to_subtract = 365
        if date.year % 4 == 0:  # If current year is leap year
            days_to_subtract = 366
        target_date = date - pd.Timedelta(days=days_to_subtract)
        # Adjust to get the same weekday
        while target_date.weekday() != date.weekday():
            target_date += pd.Timedelta(days=1)
        return target_date

    daily_summary['2024_date'] = daily_summary['day'].apply(get_same_day_previous_year)
    
    # Get data for the previous year
    available_years = sorted(price['year'].unique())
    if len(available_years) >= 2:
        prev_year = available_years[-2]  # Second to last year
    else:
        prev_year = available_years[0]  # Use the only available year
    
    data_prev_year = price[price['year'] == prev_year].copy()
    data_prev_year['day'] = data_prev_year['day'].dt.normalize()
    
    # Group previous year data by day
    daily_prev_year = data_prev_year.groupby('day').agg({
        'n_rooms': 'sum',
        'ca_room': 'sum'
    }).reset_index()
    
    # Merge previous year data with current summary
    daily_summary = pd.merge(
        daily_summary,
        daily_prev_year,
        left_on='2024_date',
        right_on='day',
        how='left',
        suffixes=('', '_prev')
    )

    # Get the current year and previous year
    current_year = str(max(available_years))
    previous_year = str(prev_year)
    
    # First rename columns for current year data
    daily_summary = daily_summary.rename(columns={
        'n_rooms': f'n_rooms_{current_year}',
        'ca_room': f'ca_room_{current_year}'
    })

    # Calculate metrics for both years, but only if the columns exist
    for year in [previous_year, current_year]:
        suffix = f'_{year}'
        # Check if both required columns exist before calculating metrics
        if f'ca_room{suffix}' in daily_summary.columns and f'n_rooms{suffix}' in daily_summary.columns:
            daily_summary[f'PM{suffix}'] = (daily_summary[f'ca_room{suffix}'] / daily_summary[f'n_rooms{suffix}']).fillna(0).round(0).astype(int)
            daily_summary[f'OR{suffix}'] = (daily_summary[f'n_rooms{suffix}'] / 70 * 100).round(1)
            daily_summary[f'ca_room{suffix}'] = daily_summary[f'ca_room{suffix}'].fillna(0).astype(int)
            daily_summary[f'n_rooms{suffix}'] = daily_summary[f'n_rooms{suffix}'].fillna(0).astype(int)

    # Calculate percentage differences only if both columns exist
    pm_current_col = f'PM_{current_year}'
    pm_prev_col = f'PM_{previous_year}'
    or_current_col = f'OR_{current_year}'
    or_prev_col = f'OR_{previous_year}'
    
    # Initialize diff columns with zeros
    daily_summary['PM_diff'] = 0
    daily_summary['OR_diff'] = 0
    
    # Only calculate if both columns exist
    if pm_current_col in daily_summary.columns and pm_prev_col in daily_summary.columns:
        # Calculate PM difference
        daily_summary['PM_diff'] = ((daily_summary[pm_current_col] / daily_summary[pm_prev_col] - 1) * 100).round(1)
        # Replace infinity and NaN with 0
        daily_summary['PM_diff'] = daily_summary['PM_diff'].replace([float('inf'), -float('inf')], 0).fillna(0)
    
    if or_current_col in daily_summary.columns and or_prev_col in daily_summary.columns:
        # Calculate OR difference
        daily_summary['OR_diff'] = ((daily_summary[or_current_col] / daily_summary[or_prev_col] - 1) * 100).round(1)
        # Replace infinity and NaN with 0
        daily_summary['OR_diff'] = daily_summary['OR_diff'].replace([float('inf'), -float('inf')], 0).fillna(0)

    # Format the differences with + sign for positive values
    daily_summary['PM_diff'] = daily_summary['PM_diff'].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
    daily_summary['OR_diff'] = daily_summary['OR_diff'].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")

    # Format OR values to always show one decimal place
    # Use the dynamic year variables we defined earlier
    for year in [previous_year, current_year]:
        column_name = f'OR_{year}'
        if column_name in daily_summary.columns:
            daily_summary[column_name] = daily_summary[column_name].apply(lambda x: f"{x:.1f}")

    daily_summary['day_display'] = daily_summary['day'].dt.strftime('%A, %B %d')
    daily_summary['day_display_2024'] = daily_summary['2024_date'].dt.strftime('%A, %B %d')
    daily_summary['Period'] = daily_summary['day'].apply(lambda date: "")
    for start, end in vacation_periods:
        daily_summary.loc[(daily_summary['day'] >= start) & (daily_summary['day'] <= end), 'Period'] = "Vacation"
    for date in public_holidays:
        daily_summary.loc[daily_summary['day'] == date, 'Period'] = "Holiday"
    for start, end, event_name, _ in special_events:
        daily_summary.loc[(daily_summary['day'] >= start) & (daily_summary['day'] <= end), 'Period'] = event_name

    # Sort by date
    daily_summary = daily_summary.sort_values('day')

    # Display the results
    st.subheader('Next 30 Days Summary with 2024 Comparison')
    
    # Prepare the display DataFrame with dynamic column selection
    columns_to_select = [
        'day_display', 'day_display_2024',
        f'n_rooms_{current_year}', f'ca_room_{current_year}', f'PM_{current_year}', f'OR_{current_year}',
        f'n_rooms_{previous_year}', f'ca_room_{previous_year}', f'PM_{previous_year}', f'OR_{previous_year}',
        'PM_diff', 'OR_diff',
        'Period'
    ]
    
    # Filter to only include columns that exist
    columns_to_select = [col for col in columns_to_select if col in daily_summary.columns]
    
    display_df = daily_summary[columns_to_select].rename(columns={
        'day_display': f'Date {current_year}',
        'day_display_2024': f'Date {previous_year}',
        f'n_rooms_{current_year}': f'Rooms {current_year}',
        f'ca_room_{current_year}': f'Revenue {current_year}',
        f'PM_{current_year}': f'PM {current_year}',
        f'OR_{current_year}': f'OR% {current_year}',
        f'n_rooms_{previous_year}': f'Rooms {previous_year}',
        f'ca_room_{previous_year}': f'Revenue {previous_year}',
        f'PM_{previous_year}': f'PM {previous_year}',
        f'OR_{previous_year}': f'OR% {previous_year}',
        'PM_diff': 'PM Diff %',
        'OR_diff': 'OR Diff %',
        'Period': 'Period'
    })

    # Create the style function
    def style_df(df):
        return df.style.apply(lambda x: [
            'background-color: #90EE90' if '+' in str(val) else 'background-color: #FFB6C6' if '-' in str(val) else ''
            for val in x
        ], subset=['PM Diff %', 'OR Diff %'])

    # Display the styled DataFrame
    st.dataframe(style_df(display_df), height=800)