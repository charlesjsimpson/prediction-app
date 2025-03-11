import pandas as pd
import numpy as np

def process_financial_data(df):
    """
    Process raw financial data to ensure it's in the correct format for analysis
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Raw financial data uploaded by the user
    
    Returns:
    --------
    pandas.DataFrame
        Processed data ready for visualization and analysis
    """
    processed_df = df.copy()
    
    # Check if date column exists, if not try to find it or create it
    if 'date' not in processed_df.columns:
        date_columns = [col for col in processed_df.columns if any(date_term in col.lower() 
                                                                 for date_term in ['date', 'period', 'month', 'year'])]
        if date_columns:
            processed_df = processed_df.rename(columns={date_columns[0]: 'date'})
        else:
            # If no date column found, create a placeholder
            processed_df['date'] = pd.date_range(start='2023-01-01', periods=len(processed_df), freq='M')
    
    # Ensure date is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(processed_df['date']):
        try:
            processed_df['date'] = pd.to_datetime(processed_df['date'])
        except Exception:
            # If conversion fails, create a placeholder
            processed_df['date'] = pd.date_range(start='2023-01-01', periods=len(processed_df), freq='M')
    
    # Check and standardize revenue columns
    revenue_columns = [col for col in processed_df.columns if any(rev_term in col.lower() 
                                                                for rev_term in ['revenue', 'sales', 'income'])]
    if revenue_columns:
        if 'revenue' not in processed_df.columns:
            # If there are multiple revenue columns, sum them
            if len(revenue_columns) > 1:
                processed_df['revenue'] = processed_df[revenue_columns].sum(axis=1)
            else:
                processed_df = processed_df.rename(columns={revenue_columns[0]: 'revenue'})
    else:
        # Create placeholder revenue data if not found
        processed_df['revenue'] = np.random.normal(100000, 10000, len(processed_df))
    
    # Check and standardize cost columns
    cost_columns = [col for col in processed_df.columns if any(cost_term in col.lower() 
                                                             for cost_term in ['cost', 'expense', 'expenditure'])]
    if cost_columns:
        if 'cost' not in processed_df.columns:
            # If there are multiple cost columns, sum them
            if len(cost_columns) > 1:
                processed_df['cost'] = processed_df[cost_columns].sum(axis=1)
            else:
                processed_df = processed_df.rename(columns={cost_columns[0]: 'cost'})
    else:
        # Create placeholder cost data if not found
        processed_df['cost'] = processed_df['revenue'] * np.random.uniform(0.6, 0.8, len(processed_df))
    
    # Calculate EBITDA if not present
    if 'ebitda' not in processed_df.columns:
        ebitda_columns = [col for col in processed_df.columns if any(ebitda_term in col.lower() 
                                                                   for ebitda_term in ['ebitda', 'profit', 'margin'])]
        if ebitda_columns:
            processed_df = processed_df.rename(columns={ebitda_columns[0]: 'ebitda'})
        else:
            processed_df['ebitda'] = processed_df['revenue'] - processed_df['cost']
    
    # Calculate profit margin if not present
    if 'profit_margin' not in processed_df.columns:
        processed_df['profit_margin'] = processed_df['ebitda'] / processed_df['revenue']
    
    # Check for revenue and cost categories
    if 'revenue_category' not in processed_df.columns:
        category_columns = [col for col in processed_df.columns if any(cat_term in col.lower() 
                                                                     for cat_term in ['category', 'type', 'segment'])]
        if category_columns:
            processed_df = processed_df.rename(columns={category_columns[0]: 'revenue_category'})
        else:
            # Create placeholder categories for hotel revenue
            hotel_categories = ['Rooms', 'Food & Beverage', 'Events', 'Spa & Wellness', 'Other']
            processed_df['revenue_category'] = np.random.choice(hotel_categories, size=len(processed_df))
    
    if 'cost_category' not in processed_df.columns:
        # Create placeholder categories for hotel costs
        hotel_cost_categories = ['Staff', 'Food & Beverage', 'Maintenance', 'Energy', 'Marketing', 'Administration']
        processed_df['cost_category'] = np.random.choice(hotel_cost_categories, size=len(processed_df))
    
    return processed_df

def generate_budget_plan(data, forecast_months=12, growth_rate=0.05):
    """
    Generate a budget plan based on historical financial data
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Processed financial data
    forecast_months : int
        Number of months to forecast
    growth_rate : float
        Expected growth rate (decimal)
    
    Returns:
    --------
    pandas.DataFrame
        Budget plan with forecasted values
    """
    # Sort data by date to ensure chronological order
    data = data.sort_values('date')
    
    # Get the last date in the dataset
    last_date = data['date'].max()
    
    # Create date range for forecast period
    forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), 
                                  periods=forecast_months, 
                                  freq='M')
    
    # Calculate average values from the last 3 months (or less if not available)
    lookback = min(3, len(data))
    recent_data = data.iloc[-lookback:]
    
    avg_revenue = recent_data['revenue'].mean()
    avg_cost = recent_data['cost'].mean()
    
    # Create forecast dataframe
    forecast_data = pd.DataFrame({
        'date': forecast_dates,
        'revenue': [avg_revenue * (1 + growth_rate) ** (i/12) for i in range(forecast_months)],
        'cost': [avg_cost * (1 + growth_rate * 0.8) ** (i/12) for i in range(forecast_months)],
    })
    
    # Calculate EBITDA and profit margin for forecast
    forecast_data['ebitda'] = forecast_data['revenue'] - forecast_data['cost']
    forecast_data['profit_margin'] = forecast_data['ebitda'] / forecast_data['revenue']
    
    # Add seasonality effect based on month (for hotels)
    # Higher revenue in summer months, lower in winter
    month_seasonality = {
        1: 0.8,  # January
        2: 0.85, # February
        3: 0.9,  # March
        4: 1.0,  # April
        5: 1.05, # May
        6: 1.15, # June
        7: 1.25, # July
        8: 1.25, # August
        9: 1.1,  # September
        10: 1.0, # October
        11: 0.9, # November
        12: 0.85 # December
    }
    
    # Apply seasonality
    for i, row in forecast_data.iterrows():
        month = row['date'].month
        season_factor = month_seasonality.get(month, 1.0)
        forecast_data.loc[i, 'revenue'] *= season_factor
        # Costs are less affected by seasonality
        forecast_data.loc[i, 'cost'] *= (1 + (season_factor - 1) * 0.5)
        # Recalculate EBITDA and profit margin
        forecast_data.loc[i, 'ebitda'] = forecast_data.loc[i, 'revenue'] - forecast_data.loc[i, 'cost']
        forecast_data.loc[i, 'profit_margin'] = forecast_data.loc[i, 'ebitda'] / forecast_data.loc[i, 'revenue']
    
    # Round values for better readability
    forecast_data['revenue'] = forecast_data['revenue'].round(2)
    forecast_data['cost'] = forecast_data['cost'].round(2)
    forecast_data['ebitda'] = forecast_data['ebitda'].round(2)
    forecast_data['profit_margin'] = forecast_data['profit_margin'].round(4)
    
    # Combine historical and forecast data if needed
    # budget_plan = pd.concat([data, forecast_data], ignore_index=True)
    
    return forecast_data

def generate_hotel_kpis(data):
    """
    Generate hotel-specific KPIs from financial data
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Processed financial data
    
    Returns:
    --------
    dict
        Dictionary of KPIs
    """
    # Calculate key hotel metrics
    kpis = {}
    
    # Average metrics
    kpis['avg_revenue'] = data['revenue'].mean()
    kpis['avg_cost'] = data['cost'].mean()
    kpis['avg_ebitda'] = data['ebitda'].mean()
    kpis['avg_profit_margin'] = data['profit_margin'].mean()
    
    # Growth rates (if time series data available)
    if len(data) > 1:
        kpis['revenue_growth'] = (data['revenue'].iloc[-1] / data['revenue'].iloc[0] - 1) * 100
        kpis['cost_growth'] = (data['cost'].iloc[-1] / data['cost'].iloc[0] - 1) * 100
        kpis['ebitda_growth'] = (data['ebitda'].iloc[-1] / data['ebitda'].iloc[0] - 1) * 100
    
    # Hotel-specific KPIs (placeholders - would be calculated from actual data)
    kpis['occupancy_rate'] = 0.75  # 75% occupancy
    kpis['adr'] = 150  # Average Daily Rate
    kpis['revpar'] = kpis['occupancy_rate'] * kpis['adr']  # Revenue Per Available Room
    
    return kpis
