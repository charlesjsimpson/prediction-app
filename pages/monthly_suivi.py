import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from utils.page_protection import check_authentication
from utils.logging_system import log_page_access, log_data_operation, log_error, log_action
from fetch_data.fetch_data_PU import price  # Adjusted import path
#from fetch_data.fetch_data_OTA_Accor import tarifs_df, tarifs_df_1  # Adjusted import path

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
log_page_access("Monthly Tracking Dashboard")

# Set page configuration
st.set_page_config(
    page_title="Pricing follow-up",  # Change this to your desired title
    layout="wide",              # Use wide layout to utilize full width
    initial_sidebar_state="expanded"  # Set sidebar to be expanded initially
)

# Set the title of the page
st.title("Suivi mensuel")

# Add a title for the Streamlit app
st.title("Monthly Summary Analysis")

# Add space between the two tabs
st.write("")  # This adds a blank line for spacing

# Change the order of the tabs
tabs = ['Monthly', 'Yearly']  # Adjust the tab order to put Variations first

# Create tabs in the Streamlit app
selected_tab = st.tabs(tabs)

#st.write(price.sample(2).to_html(escape=False, index=False), unsafe_allow_html=True)

try:
    log_data_operation("processing", "price data", "Processing date columns")
    price['day'] = pd.to_datetime(price['day'], format='%d-%m-%Y', errors='coerce')
    price['month'] = pd.to_datetime(price['day'], format='%m-%Y', errors='coerce')
    #price['month_of_year'] = pd.to_datetime(price['month'], format='%m-%Y').dt.month
    price['month_name'] = price['month'].dt.strftime('%B')
    log_data_operation("processed", "price data", "Successfully processed date columns")
except Exception as e:
    error_msg = f"Error processing date columns: {e}"
    log_error(error_msg, e)
    st.error(error_msg)
    st.stop()


with selected_tab[0]:  # Variations tab
    try:
        log_action("Viewing monthly tab")
        # Prepare the price_summary DataFrame
        #   st.write(price.sample(2))
        # Ensure the 'year' column is available
        price['year'] = price['day'].dt.year
        log_data_operation("extracted", "year data", "Extracted year from date column")
    
        # Group by month_name and year, then sum n_rooms and ca_room
        log_data_operation("aggregating", "monthly summary", "Grouping data by month and year")
        monthly_summary = price.groupby(['month_name', 'year']).agg({'n_rooms': 'sum', 'ca_room': 'sum'}).reset_index()
        log_data_operation("aggregated", "monthly summary", f"Created summary with {len(monthly_summary)} records")

        # Pivot the DataFrame to have separate columns for each year
        monthly_summary_pivot = monthly_summary.pivot(index='month_name', columns='year', values=['n_rooms', 'ca_room'])

        # Flatten the MultiIndex columns
        monthly_summary_pivot.columns = [f'{col[0]}_{col[1]}' for col in monthly_summary_pivot.columns]

        # Reset index to make 'month_name' a column again
        monthly_summary_pivot.reset_index(inplace=True)

        # Define the order of the months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']

        # Set month_name as a categorical type with the specified order
        monthly_summary_pivot['month_name'] = pd.Categorical(monthly_summary_pivot['month_name'], categories=month_order, ordered=True)

        # Sort the DataFrame by month_name
        monthly_summary_pivot.sort_values('month_name', inplace=True)

        # Ensure NaN values are replaced with 0 for n_rooms and ca_room before converting to integers
        monthly_summary_pivot[['n_rooms_2023', 'n_rooms_2024', 'n_rooms_2025', 'ca_room_2023', 'ca_room_2024', 'ca_room_2025']] = monthly_summary_pivot[['n_rooms_2023', 'n_rooms_2024', 'n_rooms_2025', 'ca_room_2023', 'ca_room_2024', 'ca_room_2025']].fillna(0)

        # Convert n_rooms and ca_room columns to integers
        monthly_summary_pivot[['n_rooms_2023', 'n_rooms_2024', 'n_rooms_2025', 'ca_room_2023', 'ca_room_2024', 'ca_room_2025']] = monthly_summary_pivot[['n_rooms_2023', 'n_rooms_2024', 'n_rooms_2025', 'ca_room_2023', 'ca_room_2024', 'ca_room_2025']].astype(int)

        # Round the values in the DataFrame to the nearest integer
        monthly_summary_pivot[['ca_room_2023', 'ca_room_2024', 'ca_room_2025']] = monthly_summary_pivot[['ca_room_2023', 'ca_room_2024', 'ca_room_2025']].round(0).astype(int)

        # Add a row for the sum of each column
        sum_row = monthly_summary_pivot[['n_rooms_2023', 'n_rooms_2024', 'n_rooms_2025', 'ca_room_2023', 'ca_room_2024', 'ca_room_2025']].sum()

        # Round the OR values to the nearest integer
        sum_row['ca_room_2023'] = round(sum_row['ca_room_2023'])
        sum_row['ca_room_2024'] = round(sum_row['ca_room_2024'])
        sum_row['ca_room_2025'] = round(sum_row['ca_room_2025'])

        # Append the sum row to the DataFrame
        sum_row['month_name'] = 'Total'
        monthly_summary_pivot = monthly_summary_pivot._append(sum_row, ignore_index=True)

        # Calculate variations and add new columns
        monthly_summary_pivot['ca_room_variation_25_24'] = (
            (monthly_summary_pivot['ca_room_2025'] - monthly_summary_pivot['ca_room_2024']) / monthly_summary_pivot['ca_room_2024']
        ) * 100

        monthly_summary_pivot['n_rooms_variation_25_24'] = (
            (monthly_summary_pivot['n_rooms_2025'] - monthly_summary_pivot['n_rooms_2024']) / monthly_summary_pivot['n_rooms_2024']
        ) * 100

        # Optional: Round the variations to one decimal place
        monthly_summary_pivot['ca_room_variation_25_24'] = monthly_summary_pivot['ca_room_variation_25_24'].round(1)
        monthly_summary_pivot['n_rooms_variation_25_24'] = monthly_summary_pivot['n_rooms_variation_25_24'].round(1)

        # Make the total row bold in the HTML output
        monthly_summary_pivot_html = monthly_summary_pivot.to_html(escape=False, index=False)
        monthly_summary_pivot_html = monthly_summary_pivot_html.replace('<tr><td>Total</td>', '<tr style="font-weight: bold;"><td>Total</td>')

        # Display the summary
        st.title("Key KPIs")
        st.write(monthly_summary_pivot_html, unsafe_allow_html=True)
        log_action("Displayed KPI summary table")

        # Define the number of days for each month
        days_in_month = {
            'January': 31,
            'February': 28,  # Adjust for leap year if necessary
            'March': 31,
            'April': 30,
            'May': 31,
            'June': 30,
            'July': 31,
            'August': 31,
            'September': 30,
            'October': 31,
            'November': 30,
            'December': 31
        }

        # Create a new DataFrame for rations using total values
        rations = pd.DataFrame({
            'Month': list(monthly_summary_pivot['month_name'])[:-1],
            'Number of Days': list(days_in_month.values()),
            'n_rooms_2023': list(monthly_summary_pivot['n_rooms_2023'])[:-1],
            'n_rooms_2024': list(monthly_summary_pivot['n_rooms_2024'])[:-1],
            'n_rooms_2025': list(monthly_summary_pivot['n_rooms_2025'])[:-1],
            'ca_room_2023': list(monthly_summary_pivot['ca_room_2023'])[:-1],
            'ca_room_2024': list(monthly_summary_pivot['ca_room_2024'])[:-1],
            'ca_room_2025': list(monthly_summary_pivot['ca_room_2025'])[:-1]
        })

        # Compute the required ratios and format as percentages
        rations['Ratio_n_rooms_2023'] = (rations['n_rooms_2023'] / (rations['Number of Days'] * 70)) * 100
        rations['Ratio_n_rooms_2024'] = (rations['n_rooms_2024'] / (rations['Number of Days'] * 70)) * 100
        rations['Ratio_n_rooms_2025'] = (rations['n_rooms_2025'] / (rations['Number of Days'] * 70)) * 100

        # Round to one decimal place
        rations['Ratio_n_rooms_2023'] = rations['Ratio_n_rooms_2023'].round(1)
        rations['Ratio_n_rooms_2024'] = rations['Ratio_n_rooms_2024'].round(1)
        rations['Ratio_n_rooms_2025'] = rations['Ratio_n_rooms_2025'].round(1)

        # Compute the required ratios for ca_room using the specified formula
        rations['Ratio_ca_room_2023'] = rations['ca_room_2023'] / (rations['n_rooms_2023'])
        rations['Ratio_ca_room_2024'] = rations['ca_room_2024'] / (rations['n_rooms_2024'])
        rations['Ratio_ca_room_2025'] = rations['ca_room_2025'] / (rations['n_rooms_2025'])

        # Round to one decimal place
        rations['Ratio_ca_room_2023'] = rations['Ratio_ca_room_2023'].round(1)
        rations['Ratio_ca_room_2024'] = rations['Ratio_ca_room_2024'].round(1)
        rations['Ratio_ca_room_2025'] = rations['Ratio_ca_room_2025'].round(1)

        # Drop the specified columns from the rations DataFrame
        rations = rations.drop(columns=['n_rooms_2023', 'n_rooms_2024', 'n_rooms_2025', 'ca_room_2023', 'ca_room_2024', 'ca_room_2025'])

        # Add a title for the Streamlit app
        st.title("Key ratios")
        # Display the rations DataFrame in your Streamlit app
        #st.write(rations, unsafe_allow_html=True)
        st.write(rations.to_html(escape=False, index=False), unsafe_allow_html=True)
        log_action("Displayed key ratios table")
    except Exception as e:
        error_msg = f"Error processing monthly data: {e}"
        log_error(error_msg, e)
        st.error(error_msg)
