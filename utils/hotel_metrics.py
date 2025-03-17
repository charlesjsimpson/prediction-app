import pandas as pd
from datetime import datetime

# Constants
TOTAL_ROOMS = 70  # Total number of rooms in the hotel

def get_total_rooms():
    """
    Get the total number of rooms in the hotel
    
    Returns:
        int: Total number of rooms
    """
    global TOTAL_ROOMS
    return TOTAL_ROOMS

def set_total_rooms(rooms):
    """
    Set the total number of rooms in the hotel
    
    Args:
        rooms (int): New total number of rooms
    """
    global TOTAL_ROOMS
    TOTAL_ROOMS = rooms

def get_days_in_period(start_date, end_date):
    """
    Calculate the exact number of calendar days between two dates (inclusive)
    
    Args:
        start_date (datetime): Start date of the period
        end_date (datetime): End date of the period
        
    Returns:
        int: Number of days in the period
    """
    # Add 1 to include both start and end dates in the count
    return (end_date - start_date).days + 1

def ensure_datetime(df, date_column='day'):
    """
    Ensure the date column is in datetime format
    
    Args:
        df: DataFrame containing the data
        date_column: Name of the date column
        
    Returns:
        DataFrame with date column converted to datetime
    """
    df_copy = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
    return df_copy

def get_last_update_date(df):
    """
    Get the most recent date in the dataframe
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        datetime object of the most recent date
    """
    if 'day' in df.columns:
        # Convert to datetime if it's not already
        df = ensure_datetime(df)
        return df['day'].max()
    return None

def calculate_kpis(df, year_filter=None, comparison_year=None, is_ytd=False):
    """
    Calculate KPIs with the correct occupancy rate formula
    
    Args:
        df: DataFrame containing the hotel data
        year_filter: Year to filter the data by
        comparison_year: Year to compare against
        is_ytd: Whether to calculate year-to-date KPIs
        
    Returns:
        Dictionary with KPI values and comparisons
    """
    # Filter by year if specified
    if year_filter:
        df_filtered = df[df['year'] == year_filter]
    else:
        df_filtered = df
    
    # Calculate total revenue
    total_revenue = df_filtered['ca_room'].sum()
    
    # Calculate total rooms sold
    total_rooms_sold = df_filtered['n_rooms'].sum()
    
    # Ensure day column is datetime
    df_filtered = ensure_datetime(df_filtered)
        
    # Count unique days in the dataset
    unique_days = df_filtered['day'].nunique()
    
    # Calculate total available rooms (days × 70 rooms)
    total_available_rooms = unique_days * TOTAL_ROOMS
    
    # Calculate occupancy rate correctly
    occupancy_rate = (total_rooms_sold / total_available_rooms) * 100 if total_available_rooms > 0 else 0
    
    # Calculate ADR
    adr = total_revenue / total_rooms_sold if total_rooms_sold > 0 else 0
    
    # Calculate RevPAR
    revpar = total_revenue / total_available_rooms if total_available_rooms > 0 else 0
    
    # Create KPI data structure
    kpis = {
        'Total Revenue': {'value': total_revenue, 'format': '€{:,.2f}'},
        'Rooms Sold': {'value': total_rooms_sold, 'format': '{:,}'},
        'Occupancy Rate': {'value': occupancy_rate, 'format': '{:.1f}%'},
        'Average Daily Rate': {'value': adr, 'format': '€{:.2f}'},
        'RevPAR': {'value': revpar, 'format': '€{:.2f}'}
    }
    
    # Calculate comparison if needed
    if comparison_year:
        comp_df = df[df['year'] == comparison_year]
        
        # Calculate comparison metrics
        comp_revenue = comp_df['ca_room'].sum()
        comp_rooms_sold = comp_df['n_rooms'].sum()
        
        # Ensure day column is datetime
        comp_df = ensure_datetime(comp_df)
        
        # Count unique days in the comparison dataset
        comp_unique_days = comp_df['day'].nunique()
        comp_available_rooms = comp_unique_days * TOTAL_ROOMS
        
        # Calculate comparison KPIs
        comp_occupancy = (comp_rooms_sold / comp_available_rooms) * 100 if comp_available_rooms > 0 else 0
        comp_adr = comp_revenue / comp_rooms_sold if comp_rooms_sold > 0 else 0
        comp_revpar = comp_revenue / comp_available_rooms if comp_available_rooms > 0 else 0
        
        # Calculate percentage changes
        revenue_change = ((total_revenue / comp_revenue) - 1) * 100 if comp_revenue > 0 else 0
        rooms_sold_change = ((total_rooms_sold / comp_rooms_sold) - 1) * 100 if comp_rooms_sold > 0 else 0
        occupancy_change = ((occupancy_rate / comp_occupancy) - 1) * 100 if comp_occupancy > 0 else 0
        adr_change = ((adr / comp_adr) - 1) * 100 if comp_adr > 0 else 0
        revpar_change = ((revpar / comp_revpar) - 1) * 100 if comp_revpar > 0 else 0
        
        # Add changes to KPI data
        kpis['Total Revenue']['change'] = revenue_change
        kpis['Rooms Sold']['change'] = rooms_sold_change
        kpis['Occupancy Rate']['change'] = occupancy_change
        kpis['Average Daily Rate']['change'] = adr_change
        kpis['RevPAR']['change'] = revpar_change
    
    return kpis

def filter_ytd_data(df, current_date=None):
    """
    Filter data for year-to-date comparison
    
    Args:
        df: DataFrame containing the data
        current_date: Current date to filter until (defaults to today)
        
    Returns:
        DataFrame filtered to year-to-date
    """
    if current_date is None:
        current_date = datetime.now()
    
    # Convert day column to datetime if it's not already
    df = ensure_datetime(df)
    
    # Filter data for all years up to the same date (month/day)
    current_month, current_day = current_date.month, current_date.day
    
    # Filter data up to current month/day for all years
    ytd_df = df[((df['day'].dt.month < current_month) | 
                ((df['day'].dt.month == current_month) & 
                 (df['day'].dt.day <= current_day)))]
    
    return ytd_df

def calculate_monthly_kpis(df, year, ytd_comparison=False, current_date=None):
    """
    Calculate monthly KPIs for a specific year
    
    Args:
        df: DataFrame containing the data
        year: Year to calculate KPIs for
        ytd_comparison: Whether to filter for year-to-date comparison
        current_date: Current date for YTD filtering
        
    Returns:
        DataFrame with monthly KPIs
    """
    # Filter data for the specified year
    year_data = df[df['year'] == year]
    
    # Apply YTD filtering if needed
    if ytd_comparison and current_date:
        year_data = filter_ytd_data(year_data, current_date)
    
    # Ensure day column is datetime
    year_data = ensure_datetime(year_data)
    
    # Group by month
    monthly_kpis = year_data.groupby('month').agg({
        'ca_room': 'sum',  # Total revenue
        'n_rooms': 'sum',   # Rooms sold
        'day': 'count'      # Days in month with data
    }).reset_index()
    
    # Add month name
    monthly_kpis['month_name'] = monthly_kpis['month'].apply(lambda x: datetime(2023, x, 1).strftime('%B'))
    
    # Get the actual number of days in each month for the selected year
    monthly_kpis['days_in_month'] = monthly_kpis['month'].apply(
        lambda x: (datetime(year, x % 12 + 1, 1) - datetime(year, x, 1)).days if x < 12 
        else (datetime(year + 1, 1, 1) - datetime(year, x, 1)).days
    )
    
    # Calculate ADR
    monthly_kpis['adr'] = monthly_kpis['ca_room'] / monthly_kpis['n_rooms']
    
    # Calculate occupancy rate using total available rooms (days in month * 70 rooms)
    monthly_kpis['occupancy_rate'] = (monthly_kpis['n_rooms'] / (monthly_kpis['days_in_month'] * TOTAL_ROOMS)) * 100
    
    # Calculate RevPAR
    monthly_kpis['revpar'] = monthly_kpis['ca_room'] / (monthly_kpis['days_in_month'] * TOTAL_ROOMS)
    
    return monthly_kpis

def format_currency(value):
    """Format value as currency"""
    return f"€{value:,.2f}"

def format_percentage(value):
    """Format value as percentage"""
    return f"{value:.1f}%"

def format_change(value):
    """Format value as change percentage with sign"""
    return f"{value:+.1f}%"

def get_month_order():
    """Get the order of months for sorting"""
    return [datetime(2023, i, 1).strftime('%B') for i in range(1, 13)]

def get_insights(df, year):
    """
    Generate basic insights from the data
    
    Args:
        df: DataFrame containing the data
        year: Year to generate insights for
        
    Returns:
        Dictionary with insights
    """
    year_data = df[df['year'] == year]
    
    # Best performing month
    best_month_idx = year_data.groupby('month')['ca_room'].sum().idxmax()
    best_month_name = datetime(2023, best_month_idx, 1).strftime('%B')
    best_month_revenue = year_data.groupby('month')['ca_room'].sum().max()
    
    # Worst performing month
    worst_month_idx = year_data.groupby('month')['ca_room'].sum().idxmin()
    worst_month_name = datetime(2023, worst_month_idx, 1).strftime('%B')
    worst_month_revenue = year_data.groupby('month')['ca_room'].sum().min()
    
    # Average occupancy
    year_data = ensure_datetime(year_data)
    unique_days = year_data['day'].nunique()
    avg_occupancy = (year_data['n_rooms'].sum() / (TOTAL_ROOMS * unique_days)) * 100
    
    return {
        'best_month': {
            'name': best_month_name,
            'revenue': best_month_revenue
        },
        'worst_month': {
            'name': worst_month_name,
            'revenue': worst_month_revenue
        },
        'avg_occupancy': avg_occupancy
    }
