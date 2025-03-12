import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

def calculate_metrics(df):
    """
    Calculate key metrics from the hotel data
    """
    metrics = {}
    
    # Basic metrics
    metrics['total_rooms'] = df['n_rooms'].sum()
    metrics['total_customers'] = df['n_customers'].sum()
    metrics['total_revenue'] = df['ca_room'].sum()
    
    # Average metrics
    metrics['avg_daily_rooms'] = df.groupby('day')['n_rooms'].sum().mean()
    metrics['avg_daily_revenue'] = df.groupby('day')['ca_room'].sum().mean()
    metrics['avg_room_price'] = df['pm'].mean()
    
    # Occupancy metrics (if we have total rooms available)
    if 'total_rooms_available' in df.columns:
        metrics['occupancy_rate'] = (df['n_rooms'].sum() / df['total_rooms_available'].sum()) * 100
    
    return metrics

def compare_years(df, year1, year2):
    """
    Compare metrics between two years
    """
    df1 = df[df['year'] == year1]
    df2 = df[df['year'] == year2]
    
    metrics1 = calculate_metrics(df1)
    metrics2 = calculate_metrics(df2)
    
    comparison = {}
    for key in metrics1.keys():
        if key in metrics2:
            comparison[key] = {
                year1: metrics1[key],
                year2: metrics2[key],
                'change': metrics2[key] - metrics1[key],
                'percent_change': ((metrics2[key] - metrics1[key]) / metrics1[key] * 100) if metrics1[key] != 0 else np.nan
            }
    
    return comparison

def plot_revenue_trend(df, period='monthly'):
    """
    Plot revenue trend by period (daily, weekly, monthly)
    """
    if period == 'daily':
        df_grouped = df.groupby('day').agg({'ca_room': 'sum'}).reset_index()
        x_col = 'day'
    elif period == 'weekly':
        df['week'] = pd.to_datetime(df['day']).dt.isocalendar().week
        df['year_week'] = df['year'].astype(str) + '-' + df['week'].astype(str)
        df_grouped = df.groupby('year_week').agg({'ca_room': 'sum'}).reset_index()
        x_col = 'year_week'
    else:  # monthly
        df_grouped = df.groupby('year_month').agg({'ca_room': 'sum'}).reset_index()
        x_col = 'year_month'
    
    fig = px.line(df_grouped, x=x_col, y='ca_room', title=f'Revenue Trend ({period})')
    fig.update_layout(xaxis_title=period.capitalize(), yaxis_title='Revenue')
    
    return fig

def plot_occupancy_by_day_of_week(df):
    """
    Plot average occupancy by day of week
    """
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    df_grouped = df.groupby('day_of_week').agg({'n_rooms': 'sum', 'n_customers': 'sum'}).reset_index()
    df_grouped['avg_customers_per_room'] = df_grouped['n_customers'] / df_grouped['n_rooms']
    
    # Reorder days
    df_grouped['day_of_week'] = pd.Categorical(df_grouped['day_of_week'], categories=days_order, ordered=True)
    df_grouped = df_grouped.sort_values('day_of_week')
    
    fig = px.bar(df_grouped, x='day_of_week', y='n_rooms', title='Room Occupancy by Day of Week')
    fig.update_layout(xaxis_title='Day of Week', yaxis_title='Number of Rooms')
    
    return fig

def plot_revenue_by_type(df):
    """
    Plot revenue breakdown by room type
    """
    df_grouped = df.groupby('type').agg({'ca_room': 'sum'}).reset_index()
    df_grouped = df_grouped.sort_values('ca_room', ascending=False)
    
    fig = px.pie(df_grouped, values='ca_room', names='type', title='Revenue by Room Type')
    
    return fig

def forecast_revenue(df, days_ahead=30):
    """
    Simple revenue forecast based on historical data
    """
    # Convert day to datetime if it's not already
    df['day'] = pd.to_datetime(df['day'])
    
    # Group by day and calculate total revenue
    daily_revenue = df.groupby('day').agg({'ca_room': 'sum'}).reset_index()
    
    # Sort by date
    daily_revenue = daily_revenue.sort_values('day')
    
    # Create a date range for forecasting
    last_date = daily_revenue['day'].max()
    forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days_ahead)
    
    # Simple moving average forecast (last 30 days)
    window_size = min(30, len(daily_revenue))
    forecast_values = [daily_revenue['ca_room'].tail(window_size).mean()] * days_ahead
    
    # Create forecast dataframe
    forecast_df = pd.DataFrame({
        'day': forecast_dates,
        'ca_room': forecast_values,
        'type': 'forecast'
    })
    
    # Combine historical and forecast data
    daily_revenue['type'] = 'historical'
    combined_df = pd.concat([daily_revenue, forecast_df])
    
    # Create plot
    fig = px.line(combined_df, x='day', y='ca_room', color='type',
                 title=f'Revenue Forecast (Next {days_ahead} Days)')
    fig.update_layout(xaxis_title='Date', yaxis_title='Revenue')
    
    return fig, forecast_df