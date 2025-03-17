import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar

# Constants
COLORS = {
    '2023': '#1f77b4',  # blue
    '2024': '#ff7f0e',  # orange
    '2025': '#2ca02c',  # green
}

# Room availability by year
ROOMS_BY_YEAR = {
    2023: 159,  # 159 rooms in 2023
    2024: 185,  # 185 rooms in 2024
    2025: 159   # 159 rooms in 2025 (default)
}

# Function to get the number of rooms for a specific year
def get_rooms_for_year(year):
    """Get the number of available rooms for a specific year"""
    return ROOMS_BY_YEAR.get(year, 70)  # Default to 70 if year not found

def create_occupancy_chart(df, time_period='monthly', year_filter=None, comparison=True):
    """
    Create occupancy rate chart based on time period
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with hotel data
    time_period : str
        Time period for aggregation ('daily', 'weekly', 'monthly', 'yearly')
    year_filter : list
        List of years to include in the chart
    comparison : bool
        Whether to show comparison between years
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure object
    """
    # Filter by year if specified
    if year_filter:
        # Convert to list if it's a single integer
        if isinstance(year_filter, int):
            year_filter = [year_filter]
        df = df[df['year'].isin(year_filter)]
    
    # Create a copy to avoid modifying the original
    data = df.copy()
    
    # Ensure date column is datetime
    data['day'] = pd.to_datetime(data['day'])
    
    # Calculate occupancy rate
    if time_period == 'daily':
        # Group by day
        grouped = data.groupby('day').agg({'n_rooms': 'sum'}).reset_index()
        grouped['year'] = grouped['day'].dt.year
        # Use the correct number of rooms for each year
        grouped['occupancy_rate'] = grouped.apply(lambda row: (row['n_rooms'] / get_rooms_for_year(row['year'])) * 100, axis=1)
        grouped['period'] = grouped['day']
        
    elif time_period == 'weekly':
        # Add week number
        data['week'] = data['day'].dt.isocalendar().week
        data['year_week'] = data['day'].dt.strftime('%Y-%U')
        
        # Group by year and week
        grouped = data.groupby(['year', 'year_week']).agg({
            'n_rooms': 'sum',
            'day': 'first'  # Take first day of the week for labeling
        }).reset_index()
        
        # Calculate weekly occupancy rate (7 days * rooms for that year)
        grouped['occupancy_rate'] = grouped.apply(lambda row: (row['n_rooms'] / (7 * get_rooms_for_year(row['year']))) * 100, axis=1)
        grouped['period'] = grouped['day'].dt.strftime('Week %U, %Y')
        
    elif time_period == 'monthly':
        # Group by year and month
        data['year_month'] = data['day'].dt.strftime('%Y-%m')
        grouped = data.groupby(['year', 'year_month']).agg({
            'n_rooms': 'sum',
            'day': 'first'  # Take first day of the month for labeling
        }).reset_index()
        
        # Calculate days in each month for accurate occupancy rate
        grouped['days_in_month'] = grouped['day'].dt.daysinmonth
        # Use the correct number of rooms for each year
        grouped['occupancy_rate'] = grouped.apply(lambda row: (row['n_rooms'] / (row['days_in_month'] * get_rooms_for_year(row['year']))) * 100, axis=1)
        grouped['period'] = grouped['day'].dt.strftime('%b %Y')
        
    else:  # yearly
        # Group by year
        grouped = data.groupby('year').agg({'n_rooms': 'sum'}).reset_index()
        
        # Calculate yearly occupancy rate (365/366 days * rooms for that year)
        grouped['days_in_year'] = grouped['year'].apply(
            lambda y: 366 if calendar.isleap(y) else 365
        )
        # Use the correct number of rooms for each year
        grouped['occupancy_rate'] = grouped.apply(lambda row: (row['n_rooms'] / (row['days_in_year'] * get_rooms_for_year(row['year']))) * 100, axis=1)
        grouped['period'] = grouped['year'].astype(str)
    
    # Create the chart
    if comparison and time_period != 'yearly':
        # For comparison between years, use line chart with year as color
        fig = px.line(
            grouped, 
            x=grouped['period'] if time_period == 'yearly' else grouped['day'],
            y='occupancy_rate',
            color=grouped['year'].astype(str),
            markers=True,
            color_discrete_map=COLORS,
            labels={'occupancy_rate': 'Occupancy Rate (%)', 'period': 'Period'},
            title=f'Hotel Occupancy Rate ({time_period.capitalize()})'
        )
        
        # Customize x-axis based on time period
        if time_period == 'monthly':
            fig.update_xaxes(
                tickformat='%b',
                tickmode='array',
                tickvals=pd.date_range(start=f"{min(grouped['year'])}-01-01", 
                                      end=f"{min(grouped['year'])}-12-01", 
                                      freq='MS')
            )
    else:
        # For single year or yearly comparison, use bar chart
        fig = px.bar(
            grouped,
            x='period',
            y='occupancy_rate',
            color='year' if time_period == 'yearly' else None,
            color_discrete_map=COLORS,
            labels={'occupancy_rate': 'Occupancy Rate (%)', 'period': 'Period'},
            title=f'Hotel Occupancy Rate ({time_period.capitalize()})'
        )
    
    # Add target line at 80% occupancy
    fig.add_hline(
        y=80, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Target (80%)",
        annotation_position="top right"
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Period',
        yaxis_title='Occupancy Rate (%)',
        legend_title='Year',
        height=500
    )
    
    return fig

def create_revenue_chart(df, time_period='monthly', year_filter=None, metric='total'):
    """
    Create revenue chart based on time period and metric
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with hotel data
    time_period : str
        Time period for aggregation ('daily', 'weekly', 'monthly', 'yearly')
    year_filter : list
        List of years to include in the chart
    metric : str
        Revenue metric to display ('total', 'per_room', 'revpar')
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure object
    """
    # Filter by year if specified
    if year_filter:
        # Convert to list if it's a single integer
        if isinstance(year_filter, int):
            year_filter = [year_filter]
        df = df[df['year'].isin(year_filter)]
    
    # Create a copy to avoid modifying the original
    data = df.copy()
    
    # Ensure date column is datetime
    data['day'] = pd.to_datetime(data['day'])
    
    # Group by the specified time period
    if time_period == 'daily':
        grouped = data.groupby(['year', 'day']).agg({
            'n_rooms': 'sum',
            'ca_room': 'sum'
        }).reset_index()
        grouped['period'] = grouped['day']
        
    elif time_period == 'weekly':
        data['week'] = data['day'].dt.isocalendar().week
        data['year_week'] = data['day'].dt.strftime('%Y-%U')
        
        grouped = data.groupby(['year', 'year_week']).agg({
            'n_rooms': 'sum',
            'ca_room': 'sum',
            'day': 'first'
        }).reset_index()
        grouped['period'] = grouped['day'].dt.strftime('Week %U, %Y')
        
    elif time_period == 'monthly':
        data['year_month'] = data['day'].dt.strftime('%Y-%m')
        grouped = data.groupby(['year', 'year_month']).agg({
            'n_rooms': 'sum',
            'ca_room': 'sum',
            'day': 'first'
        }).reset_index()
        grouped['period'] = grouped['day'].dt.strftime('%b %Y')
        grouped['days_in_month'] = grouped['day'].dt.daysinmonth
        
    else:  # yearly
        grouped = data.groupby('year').agg({
            'n_rooms': 'sum',
            'ca_room': 'sum'
        }).reset_index()
        grouped['period'] = grouped['year'].astype(str)
        grouped['days_in_year'] = grouped['year'].apply(
            lambda y: 366 if calendar.isleap(y) else 365
        )
    
    # Calculate the requested metric
    if metric == 'total':
        y_column = 'ca_room'
        title = f'Total Revenue ({time_period.capitalize()})'
        y_title = 'Revenue (€)'
    
    elif metric == 'per_room':
        grouped['revenue_per_room'] = grouped['ca_room'] / grouped['n_rooms']
        y_column = 'revenue_per_room'
        title = f'Average Revenue Per Occupied Room ({time_period.capitalize()})'
        y_title = 'Revenue Per Room (€)'
    
    elif metric == 'revpar':
        # Revenue per available room - use the correct number of rooms for each year
        if time_period == 'daily':
            grouped['revpar'] = grouped.apply(lambda row: row['ca_room'] / get_rooms_for_year(row['year']), axis=1)
        elif time_period == 'weekly':
            grouped['revpar'] = grouped.apply(lambda row: row['ca_room'] / (7 * get_rooms_for_year(row['year'])), axis=1)
        elif time_period == 'monthly':
            grouped['revpar'] = grouped.apply(lambda row: row['ca_room'] / (row['days_in_month'] * get_rooms_for_year(row['year'])), axis=1)
        else:  # yearly
            grouped['revpar'] = grouped.apply(lambda row: row['ca_room'] / (row['days_in_year'] * get_rooms_for_year(row['year'])), axis=1)
            
        y_column = 'revpar'
        title = f'Revenue Per Available Room (RevPAR) ({time_period.capitalize()})'
        y_title = 'RevPAR (€)'
    
    # Create the chart
    if time_period == 'yearly':
        # For yearly data, use bar chart
        fig = px.bar(
            grouped,
            x='period',
            y=y_column,
            color='year',
            color_discrete_map=COLORS,
            labels={y_column: y_title, 'period': 'Year'},
            title=title
        )
    else:
        # For other time periods, use line chart with year as color
        fig = px.line(
            grouped, 
            x='day',
            y=y_column,
            color=grouped['year'].astype(str),
            markers=True,
            color_discrete_map=COLORS,
            labels={y_column: y_title},
            title=title
        )
        
        # Customize x-axis based on time period
        if time_period == 'monthly':
            fig.update_xaxes(
                tickformat='%b',
                tickmode='array',
                tickvals=pd.date_range(start=f"{min(grouped['year'])}-01-01", 
                                      end=f"{min(grouped['year'])}-12-01", 
                                      freq='MS')
            )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Period',
        yaxis_title=y_title,
        legend_title='Year',
        height=500
    )
    
    return fig

def create_kpi_summary(df, year_filter=None, comparison_year=None):
    """
    Create KPI summary cards
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with hotel data
    year_filter : int
        Year to display KPIs for
    comparison_year : int
        Year to compare with
        
    Returns:
    --------
    dict
        Dictionary with KPI values and comparisons
    """
    # Filter data for the selected year
    if year_filter:
        current_data = df[df['year'] == year_filter].copy()
    else:
        # Use the most recent year if not specified
        year_filter = df['year'].max()
        current_data = df[df['year'] == year_filter].copy()
    
    # Calculate KPIs for the current year
    total_revenue = current_data['ca_room'].sum()
    total_rooms_sold = current_data['n_rooms'].sum()
    
    # Calculate days in the year
    days_in_year = 366 if calendar.isleap(year_filter) else 365
    
    # Calculate occupancy rate using the correct number of rooms for this year
    total_rooms = get_rooms_for_year(year_filter)
    occupancy_rate = (total_rooms_sold / (total_rooms * days_in_year)) * 100
    
    # Calculate average daily rate (ADR)
    adr = total_revenue / total_rooms_sold if total_rooms_sold > 0 else 0
    
    # Calculate RevPAR using the correct number of rooms
    revpar = total_revenue / (total_rooms * days_in_year)
    
    # Prepare KPI dictionary
    kpis = {
        'Total Revenue': {'value': total_revenue, 'format': '€{:,.2f}'},
        'Rooms Sold': {'value': total_rooms_sold, 'format': '{:,}'},
        'Occupancy Rate': {'value': occupancy_rate, 'format': '{:.1f}%'},
        'Average Daily Rate': {'value': adr, 'format': '€{:.2f}'},
        'RevPAR': {'value': revpar, 'format': '€{:.2f}'}
    }
    
    # Add comparison if requested
    if comparison_year:
        comparison_data = df[df['year'] == comparison_year].copy()
        
        # Calculate comparison KPIs
        comp_total_revenue = comparison_data['ca_room'].sum()
        comp_total_rooms_sold = comparison_data['n_rooms'].sum()
        
        # Calculate days in the comparison year
        comp_days_in_year = 366 if calendar.isleap(comparison_year) else 365
        
        # Calculate comparison occupancy rate using the correct number of rooms for the comparison year
        comp_total_rooms = get_rooms_for_year(comparison_year)
        comp_occupancy_rate = (comp_total_rooms_sold / (comp_total_rooms * comp_days_in_year)) * 100
        
        # Calculate comparison ADR
        comp_adr = comp_total_revenue / comp_total_rooms_sold if comp_total_rooms_sold > 0 else 0
        
        # Calculate comparison RevPAR using the correct number of rooms
        comp_revpar = comp_total_revenue / (comp_total_rooms * comp_days_in_year)
        
        # Calculate percentage changes
        kpis['Total Revenue']['change'] = ((total_revenue / comp_total_revenue) - 1) * 100 if comp_total_revenue > 0 else 0
        kpis['Rooms Sold']['change'] = ((total_rooms_sold / comp_total_rooms_sold) - 1) * 100 if comp_total_rooms_sold > 0 else 0
        kpis['Occupancy Rate']['change'] = occupancy_rate - comp_occupancy_rate
        kpis['Average Daily Rate']['change'] = ((adr / comp_adr) - 1) * 100 if comp_adr > 0 else 0
        kpis['RevPAR']['change'] = ((revpar / comp_revpar) - 1) * 100 if comp_revpar > 0 else 0
    
    return kpis

def create_occupancy_heatmap(df, year_filter=None):
    """
    Create occupancy heatmap by day of week and month
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with hotel data
    year_filter : int
        Year to display data for
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure object
    """
    # Filter data for the selected year
    if year_filter:
        data = df[df['year'] == year_filter].copy()
    else:
        # Use the most recent year if not specified
        year_filter = df['year'].max()
        data = df[df['year'] == year_filter].copy()
    
    # Ensure date column is datetime
    data['day'] = pd.to_datetime(data['day'])
    
    # Add day of week and month
    data['day_of_week'] = data['day'].dt.day_name()
    data['month'] = data['day'].dt.month_name()
    
    # Order days of week and months
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    # Group by day of week and month
    grouped = data.groupby(['day_of_week', 'month']).agg({
        'n_rooms': 'sum',
        'day': 'count'  # Count of days for each combination
    }).reset_index()
    
    # Calculate occupancy rate using the correct number of rooms for the year
    total_rooms = get_rooms_for_year(year_filter)
    grouped['occupancy_rate'] = (grouped['n_rooms'] / (grouped['day'] * total_rooms)) * 100
    
    # Create pivot table
    pivot_data = grouped.pivot_table(
        values='occupancy_rate',
        index='day_of_week',
        columns='month',
        aggfunc='mean'
    )
    
    # Reorder index and columns
    pivot_data = pivot_data.reindex(days_order)
    pivot_data = pivot_data.reindex(columns=months_order)
    
    # Create heatmap
    fig = px.imshow(
        pivot_data,
        labels=dict(x="Month", y="Day of Week", color="Occupancy Rate (%)"),
        x=pivot_data.columns,
        y=pivot_data.index,
        color_continuous_scale="RdYlGn",  # Red to Yellow to Green
        title=f'Occupancy Rate Heatmap ({year_filter})'
    )
    
    # Add text annotations
    for i, day in enumerate(pivot_data.index):
        for j, month in enumerate(pivot_data.columns):
            value = pivot_data.loc[day, month]
            if not pd.isna(value):
                fig.add_annotation(
                    x=month,
                    y=day,
                    text=f"{value:.1f}%",
                    showarrow=False,
                    font=dict(color="black" if 30 <= value <= 70 else "white")
                )
    
    # Customize layout
    fig.update_layout(
        height=500,
        coloraxis_colorbar=dict(title="Occupancy Rate (%)")
    )
    
    return fig

def create_year_comparison_chart(df, metrics=['occupancy_rate', 'adr', 'revpar']):
    """
    Create year-over-year comparison chart for selected metrics
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with hotel data
    metrics : list
        List of metrics to include in the chart
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure object
    """
    # Create a copy to avoid modifying the original
    data = df.copy()
    
    # Ensure date column is datetime
    data['day'] = pd.to_datetime(data['day'])
    
    # Group by year and month
    data['month'] = data['day'].dt.month
    grouped = data.groupby(['year', 'month']).agg({
        'n_rooms': 'sum',
        'ca_room': 'sum',
        'day': 'first'  # Take first day of the month for reference
    }).reset_index()
    
    # Calculate days in each month
    grouped['days_in_month'] = grouped['day'].dt.daysinmonth
    
    # Calculate metrics using the correct number of rooms for each year
    grouped['occupancy_rate'] = grouped.apply(lambda row: (row['n_rooms'] / (row['days_in_month'] * get_rooms_for_year(row['year']))) * 100, axis=1)
    grouped['adr'] = grouped['ca_room'] / grouped['n_rooms']
    grouped['revpar'] = grouped.apply(lambda row: row['ca_room'] / (row['days_in_month'] * get_rooms_for_year(row['year'])), axis=1)
    
    # Create month labels
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    grouped['month_name'] = grouped['month'].map(month_names)
    
    # Create subplots
    fig = make_subplots(
        rows=len(metrics),
        cols=1,
        subplot_titles=[m.replace('_', ' ').title() for m in metrics],
        shared_xaxes=True,
        vertical_spacing=0.1
    )
    
    # Add traces for each year and metric
    for i, year in enumerate(sorted(grouped['year'].unique())):
        year_data = grouped[grouped['year'] == year]
        
        for j, metric in enumerate(metrics):
            fig.add_trace(
                go.Scatter(
                    x=year_data['month_name'],
                    y=year_data[metric],
                    mode='lines+markers',
                    name=f'{year} - {metric.replace("_", " ").title()}',
                    line=dict(color=COLORS.get(str(year), px.colors.qualitative.Plotly[i % 10])),
                    showlegend=j == 0,  # Only show in legend for the first metric
                ),
                row=j+1,
                col=1
            )
    
    # Update y-axis titles
    y_titles = {
        'occupancy_rate': 'Occupancy Rate (%)',
        'adr': 'ADR (€)',
        'revpar': 'RevPAR (€)'
    }
    
    for i, metric in enumerate(metrics):
        fig.update_yaxes(title_text=y_titles.get(metric, metric.title()), row=i+1, col=1)
    
    # Update layout
    fig.update_layout(
        title='Year-over-Year Comparison by Month',
        xaxis=dict(
            title='Month',
            tickmode='array',
            tickvals=list(month_names.values())
        ),
        height=300 * len(metrics),
        legend_title='Year',
        hovermode='x unified'
    )
    
    return fig