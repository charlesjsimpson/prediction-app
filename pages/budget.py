import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import calendar
import plotly.express as px
from utils.page_protection import check_authentication
from utils.logging_system import log_page_access, log_data_operation, log_error, log_action
from fetch_data.fetch_data_PU import load_data

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
log_page_access("Budget Planning")

# Set page configuration
st.set_page_config(
    page_title="Budget Planning",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set page title and header
st.title("Budget Planning & Forecasting")

# Load the data
try:
    log_data_operation("loading", "price data")
    price, df_1 = load_data()
    
    # Combine the dataframes if df_1 is not empty
    if not df_1.empty:
        price = pd.concat([price, df_1], ignore_index=True)
        log_data_operation("combining", "price data", "Combined multiple dataframes")
    
    # Verify that required columns exist
    required_columns = ['month', 'month_name', 'year']
    for col in required_columns:
        if col not in price.columns:
            log_error(f"Missing required column: {col}", Exception(f"Column {col} not found in price DataFrame"))
            st.error(f"Error: Missing required column '{col}' in data. Please check the data source.")
            st.stop()
    
    log_data_operation("loaded", "price data", f"Successfully loaded {len(price)} records with {len(price.columns)} columns")
except Exception as e:
    error_msg = f"Error loading data: {e}"
    log_error(error_msg, e)
    st.error(error_msg)
    st.stop()

# Create tabs for different budget functions
tab_overview, tab_forecast, tab_budget_vs_actual, tab_budget_creation = st.tabs([
    "Budget Overview", "Revenue Forecast", "Budget vs. Actual", "Create Budget"
])

# Helper functions for budget calculations
def calculate_monthly_budget(df, year, month, growth_rate=0.05):
    """Calculate budget based on previous year data with growth rate"""
    # Filter data for the previous year and month
    prev_year = year - 1
    prev_year_data = df[(df['year'] == prev_year) & (df['month'] == month)]
    
    if prev_year_data.empty:
        # If no data for previous year, use average of available data
        avg_data = df[df['month'] == month].groupby('year').agg({
            'ca_room': 'sum',
            'n_rooms': 'sum'
        }).mean()
        
        if avg_data.empty:
            # If still no data, return zeros
            return {
                'year': year,
                'month': month,
                'budget_revenue': 0,
                'budget_rooms': 0,
                'budget_adr': 0
            }
        
        budget_revenue = avg_data['ca_room'] * (1 + growth_rate)
        budget_rooms = avg_data['n_rooms']
    else:
        # Calculate budget based on previous year with growth
        budget_revenue = prev_year_data['ca_room'].sum() * (1 + growth_rate)
        budget_rooms = prev_year_data['n_rooms'].sum()
    
    # Calculate ADR (Average Daily Rate)
    budget_adr = budget_revenue / budget_rooms if budget_rooms > 0 else 0
    
    return {
        'year': year,
        'month': month,
        'budget_revenue': budget_revenue,
        'budget_rooms': budget_rooms,
        'budget_adr': budget_adr
    }

def generate_annual_budget(df, year, growth_rate=0.05):
    """Generate a budget for the entire year"""
    budget_data = []
    
    for month in range(1, 13):
        monthly_budget = calculate_monthly_budget(df, year, month, growth_rate)
        budget_data.append(monthly_budget)
    
    return pd.DataFrame(budget_data)

def forecast_revenue(df, months_ahead=3):
    """Forecast revenue for the next few months"""
    # Get the most recent data
    latest_date = df['day'].max()
    latest_year = latest_date.year
    latest_month = latest_date.month
    
    forecast_data = []
    
    # Generate forecast for the next few months
    for i in range(1, months_ahead + 1):
        # Calculate the target month and year
        target_month = (latest_month + i) % 12
        if target_month == 0:
            target_month = 12
        target_year = latest_year + ((latest_month + i - 1) // 12)
        
        # Calculate the budget for this month
        monthly_forecast = calculate_monthly_budget(df, target_year, target_month)
        
        # Add month name for display
        monthly_forecast['month_name'] = calendar.month_name[target_month]
        forecast_data.append(monthly_forecast)
    
    return pd.DataFrame(forecast_data)

# Function to load or create budget data
def load_budget_data(year):
    """Load budget data from file or create if not exists"""
    budget_file = os.path.join(root_dir, 'data', f'budget_{year}.csv')
    
    try:
        if os.path.exists(budget_file):
            # Load existing budget
            log_data_operation("loading", f"budget_{year}", f"Loading existing budget from {budget_file}")
            return pd.read_csv(budget_file)
        else:
            # Create new budget based on historical data
            log_data_operation("generating", f"budget_{year}", "Creating new budget based on historical data")
            return generate_annual_budget(price, year)
    except Exception as e:
        error_msg = f"Error loading budget data for {year}: {e}"
        log_error(error_msg, e)
        raise

def save_budget_data(budget_df, year):
    """Save budget data to CSV file"""
    # Create data directory if it doesn't exist
    data_dir = os.path.join(root_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Save to CSV
    budget_file = os.path.join(data_dir, f'budget_{year}.csv')
    try:
        budget_df.to_csv(budget_file, index=False)
        log_data_operation("saved", f"budget_{year}", f"Budget data saved to {budget_file}")
        return budget_file
    except Exception as e:
        error_msg = f"Error saving budget data: {e}"
        log_error(error_msg, e)
        raise
# Budget Overview Tab
with tab_overview:
    st.header("Budget Overview")
    
    # Select year for budget overview
    current_year = datetime.now().year
    year_options = list(range(current_year - 2, current_year + 2))
    selected_year = st.selectbox("Select Year", year_options, index=year_options.index(current_year))
    
    # Load or generate budget data
    budget_data = load_budget_data(selected_year)
    
    # Display budget summary
    st.subheader(f"Budget Summary for {selected_year}")
    
    # Calculate totals
    total_budget_revenue = budget_data['budget_revenue'].sum()
    total_budget_rooms = budget_data['budget_rooms'].sum()
    avg_budget_adr = total_budget_revenue / total_budget_rooms if total_budget_rooms > 0 else 0
    
    # Create metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Budget Revenue", f"€{total_budget_revenue:,.2f}")
    col2.metric("Total Budget Room Nights", f"{total_budget_rooms:,.0f}")
    col3.metric("Average Budget ADR", f"€{avg_budget_adr:,.2f}")
    
    # Create a bar chart for monthly budget
    budget_data['month_name'] = budget_data['month'].apply(lambda x: calendar.month_name[x])
    
    # Plot monthly budget revenue
    fig = px.bar(
        budget_data,
        x='month_name',
        y='budget_revenue',
        title=f"Monthly Budget Revenue for {selected_year}",
        labels={'budget_revenue': 'Budget Revenue (€)', 'month_name': 'Month'},
        color_discrete_sequence=['#3366CC']
    )
    st.plotly_chart(fig, use_container_width=True)
    # Plot monthly budget rooms
    fig2 = px.bar(
        budget_data,
        x='month_name',
        y='budget_rooms',
        title=f"Monthly Budget Room Nights for {selected_year}",
        labels={'budget_rooms': 'Budget Room Nights', 'month_name': 'Month'},
        color_discrete_sequence=['#33CC99']
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Display the budget data table
    st.subheader("Monthly Budget Details")
    display_budget = budget_data.copy()
    display_budget['budget_revenue'] = display_budget['budget_revenue'].map('€{:,.2f}'.format)
    display_budget['budget_adr'] = display_budget['budget_adr'].map('€{:,.2f}'.format)
    display_budget = display_budget[['month_name', 'budget_revenue', 'budget_rooms', 'budget_adr']]
    display_budget.columns = ['Month', 'Budget Revenue', 'Budget Room Nights', 'Budget ADR']
    st.dataframe(display_budget, use_container_width=True)

# Revenue Forecast Tab
with tab_forecast:
    st.header("Revenue Forecast")
    
    # Options for forecast
    forecast_months = st.slider("Months to Forecast", 1, 12, 3)
    growth_rate = st.slider("Growth Rate (%)", -10.0, 20.0, 5.0) / 100
    
    # Generate forecast
    forecast_data = forecast_revenue(price, forecast_months)
    forecast_data['growth_rate'] = growth_rate
    
    # Apply growth rate to forecast
    forecast_data['budget_revenue'] = forecast_data['budget_revenue'] * (1 + growth_rate)
    forecast_data['budget_adr'] = forecast_data['budget_adr'] * (1 + growth_rate)
    
    # Display forecast
    st.subheader(f"Revenue Forecast for Next {forecast_months} Months")
    
    # Create forecast visualization
    fig = px.bar(
        forecast_data,
        x='month_name',
        y='budget_revenue',
        title=f"Forecasted Revenue (Growth Rate: {growth_rate:.1%})",
        labels={'budget_revenue': 'Forecasted Revenue (€)', 'month_name': 'Month'},
        color_discrete_sequence=['#FF9900']
    )
    st.plotly_chart(fig, use_container_width=True)
