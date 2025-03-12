import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import extra_streamlit_components as stx
import datetime
from pathlib import Path

# Import utility functions
from utils.data_processing import process_financial_data, generate_budget_plan
from utils.authentication import check_authentication, create_user

def run_app():
    # Page configuration is now handled in streamlit_app.py
    # Do not call st.set_page_config() here as it's already called in the main entry point

    # Create necessary directories if they don't exist
    Path("data").mkdir(exist_ok=True)
    Path("data/uploads").mkdir(exist_ok=True)
    Path("data/reports").mkdir(exist_ok=True)

    # Initialize cookie manager for authentication
    cookie_manager = stx.CookieManager()
    cookies = cookie_manager.get_all()

    # Authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    # Check if user is already authenticated via cookie
    if not st.session_state.authenticated and cookies.get("auth_token"):
        auth_result = check_authentication(cookies.get("auth_token"))
        if auth_result["success"]:
            st.session_state.authenticated = True
            st.session_state.username = auth_result["username"]

    # Display login/signup form if not authenticated
    if not st.session_state.authenticated:
        st.title("Hotel Financial Dashboard")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    auth_result = check_authentication(username, password)
                    if auth_result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        cookie_manager.set("auth_token", auth_result["token"], expires_at=datetime.datetime.now() + datetime.timedelta(days=7))
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password")
    
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit_signup = st.form_submit_button("Sign Up")
                
                if submit_signup:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        result = create_user(new_username, new_password)
                        if result["success"]:
                            st.success("Account created successfully! Please login.")
                        else:
                            st.error(result["message"])

    else:
        # Main application interface when authenticated
        st.sidebar.title(f"Welcome, {st.session_state.username}!")
        
        # Main content
        st.title("Hotel Financial Dashboard & Business Planning")
        
        # File upload section
        st.header("Upload Financial Data")
        uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
        
        if uploaded_file is not None:
            try:
                # Determine file type and read accordingly
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
            
                # Display raw data
                st.subheader("Raw Data Preview")
                st.dataframe(df)
                
                # Process the financial data
                processed_data = process_financial_data(df)
                
                # Visualization section
                st.header("Financial Analysis")
                
                # Create tabs for different visualizations
                tab1, tab2, tab3 = st.tabs(["Revenue Analysis", "Cost Analysis", "Profitability"])
            
                with tab1:
                    st.subheader("Revenue Trends")
                    if 'date' in processed_data.columns and 'revenue' in processed_data.columns:
                        fig = px.line(processed_data, x='date', y='revenue', title='Revenue Over Time')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Revenue Breakdown")
                    if 'revenue_category' in processed_data.columns and 'revenue' in processed_data.columns:
                        fig = px.pie(processed_data, values='revenue', names='revenue_category', title='Revenue by Category')
                        st.plotly_chart(fig, use_container_width=True)
            
                with tab2:
                    st.subheader("Cost Structure")
                    if 'cost_category' in processed_data.columns and 'cost' in processed_data.columns:
                        fig = px.pie(processed_data, values='cost', names='cost_category', title='Costs by Category')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Cost Trends")
                    if 'date' in processed_data.columns and 'cost' in processed_data.columns:
                        fig = px.line(processed_data, x='date', y='cost', title='Costs Over Time')
                        st.plotly_chart(fig, use_container_width=True)
            
                with tab3:
                    st.subheader("Profitability Metrics")
                    if 'date' in processed_data.columns and 'ebitda' in processed_data.columns:
                        fig = px.line(processed_data, x='date', y='ebitda', title='EBITDA Over Time')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    if 'date' in processed_data.columns and 'profit_margin' in processed_data.columns:
                        fig = px.line(processed_data, x='date', y='profit_margin', title='Profit Margin Over Time')
                        st.plotly_chart(fig, use_container_width=True)
            
                # Business Planning section
                st.header("Business Planning")
                
                st.subheader("Generate Budget Plan")
                forecast_months = st.slider("Forecast Period (months)", min_value=3, max_value=36, value=12)
                growth_rate = st.slider("Expected Growth Rate (%)", min_value=-20, max_value=50, value=5)
            
                if st.button("Generate Budget Plan"):
                    with st.spinner("Generating budget plan..."):
                        budget_plan = generate_budget_plan(processed_data, forecast_months, growth_rate/100)
                        
                        st.subheader("Budget Forecast")
                        st.dataframe(budget_plan)
                        
                        # Visualize the budget plan
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=budget_plan['date'], y=budget_plan['revenue'], mode='lines', name='Revenue'))
                        fig.add_trace(go.Scatter(x=budget_plan['date'], y=budget_plan['cost'], mode='lines', name='Cost'))
                        fig.add_trace(go.Scatter(x=budget_plan['date'], y=budget_plan['ebitda'], mode='lines', name='EBITDA'))
                        fig.update_layout(title='Budget Forecast', xaxis_title='Date', yaxis_title='Amount')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Download button for the budget plan
                        csv = budget_plan.to_csv(index=False)
                        st.download_button(
                            label="Download Budget Plan as CSV",
                            data=csv,
                            file_name=f"budget_plan_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
            
                # AI-powered business insights section
                st.header("AI Business Insights")
                if st.button("Generate Business Insights"):
                    with st.spinner("Analyzing data and generating insights..."):
                        # Here we would integrate with an LLM like ChatGPT or Mistral
                        # For now, we'll just display a placeholder
                        st.info("This feature will use an LLM to provide business insights based on your financial data.")
                        st.markdown("""
                        **Sample Insights:**
                        1. Your hotel shows seasonal revenue patterns with peaks in summer months
                        2. Room service contributes significantly to your revenue stream
                        3. Energy costs are increasing year over year
                        4. Consider investing in energy-efficient solutions to reduce operational costs
                        """)
        
            except Exception as e:
                st.error(f"Error processing the file: {e}")
    
        else:
            # Show sample data option when no file is uploaded
            if st.button("Use Sample Data"):
                # Load sample data
                sample_data = {
                    'date': pd.date_range(start='2023-01-01', periods=12, freq='M'),
                    'revenue': [100000, 95000, 105000, 115000, 125000, 140000, 150000, 145000, 130000, 120000, 110000, 105000],
                    'cost': [70000, 68000, 72000, 75000, 80000, 85000, 90000, 88000, 82000, 78000, 75000, 73000],
                    'ebitda': [30000, 27000, 33000, 40000, 45000, 55000, 60000, 57000, 48000, 42000, 35000, 32000],
                    'revenue_category': ['Rooms', 'F&B', 'Events', 'Spa', 'Rooms', 'F&B', 'Events', 'Spa', 'Rooms', 'F&B', 'Events', 'Spa'],
                    'cost_category': ['Staff', 'F&B', 'Maintenance', 'Energy', 'Staff', 'F&B', 'Maintenance', 'Energy', 'Staff', 'F&B', 'Maintenance', 'Energy'],
                    'profit_margin': [0.3, 0.28, 0.31, 0.35, 0.36, 0.39, 0.4, 0.39, 0.37, 0.35, 0.32, 0.3]
                }
                df = pd.DataFrame(sample_data)
                st.session_state.sample_data = df
                st.experimental_rerun()
            
            # Display instructions
            st.info("Please upload a CSV or Excel file with your hotel's financial data, or use the sample data option to explore the dashboard features.")
            st.markdown("""
            **Expected data format:**
            - Date column (monthly or quarterly periods)
            - Revenue figures (total and/or by category)
            - Cost figures (total and/or by category)
            - EBITDA or profit figures
            
            The dashboard will automatically process your data and generate visualizations and forecasts.
            """)

# If this file is run directly, execute the app
if __name__ == "__main__":
    run_app()
