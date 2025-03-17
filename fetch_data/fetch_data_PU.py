import os
import pandas as pd
from pathlib import Path

# Define the directory containing the files
project_root = Path(__file__).parent.parent
data_root = os.path.join(project_root, 'data')

# List of main files to process
file_names = ["2023_PU.xlsx", "2024_PU.xlsx", "2025_PU_03_17.xlsx"]  # Updated to use the latest file

# Name of the file to process separately
separate_file = "2025_02_12_PU.xlsx"

# Function to transform the DataFrame
def transform_dataframe(df):
    # Rename columns for better readability
    df.rename(
        columns={
            "Date": "day",
            "Type.1": "type",
            "Sous Type": "sous_type",
            "Nbre Ch.": "n_rooms",
            "Nbre Clients": "n_customers",
            "Room_PM": "pm",
            "C.A. Chambre": "ca_room",
            "PM Total Chambre": "pm",
            "C.A. Total": "ca_tol",
            "% C.A. / C.A. Général": "% C.A. / C.A. Général",
            "Nb CH Facturées": "Nb_room_billed",
            "% C.A. / C.A. / C.A. GÇnÇral": "% C.A. / C.A. GÇnÇral",  # Corrected column name
        },
        inplace=True
    )

    # Keep only the necessary columns and make an explicit copy to avoid SettingWithCopyWarning
    df = df[['day', 'type', 'sous_type', 'n_rooms', 'n_customers', 'ca_room', 'pm', 'Source_File']].copy()

    # Create a datetime column to avoid repeated conversions
    datetime_col = pd.to_datetime(df['day'], errors='coerce')
    
    # Add new columns
    df['year'] = datetime_col.dt.year
    df['month'] = datetime_col.dt.month
    df['month_name'] = datetime_col.dt.month_name()
    df['year_month'] = datetime_col.dt.to_period('M').astype(str)
    df['day_of_week'] = datetime_col.dt.day_name()

    return df

# Function to load data
def load_data():
    """Load and process hotel data from Excel files.
    
    Returns:
        tuple: A tuple containing two DataFrames:
            - price: Combined data from all main files
            - df_1: Data from the separate file (or empty DataFrame if file doesn't exist)
    """
    dataframe_list = []

    # Common Excel reading parameters
    excel_params = {
        'sheet_name': 0,     # Read the first sheet
        'skiprows': 1,       # Skip the first row
        'engine': 'openpyxl' # Use the openpyxl engine
    }

    # Iterate through each main file and load it into a DataFrame
    for file_name in file_names:
        file_path = os.path.join(data_root, file_name)
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, **excel_params)
                df['Source_File'] = file_name  # Add a column indicating the source file
                dataframe_list.append(df)  # Add the DataFrame to the list
            except Exception as e:
                print(f"Error reading file {file_name}: {e}")

    # Aggregate all main DataFrames into one
    price = pd.concat(dataframe_list, ignore_index=True) if dataframe_list else pd.DataFrame()

    # Load the separate file
    separate_file_path = os.path.join(data_root, separate_file)
    if os.path.exists(separate_file_path):
        try:
            df_1 = pd.read_excel(separate_file_path, **excel_params)
            df_1['Source_File'] = separate_file  # Add a column indicating the source file
        except Exception as e:
            print(f"Error reading separate file {separate_file}: {e}")
            df_1 = pd.DataFrame()
    else:
        df_1 = pd.DataFrame()  # Create an empty DataFrame if the file does not exist

    # Transform the DataFrames
    if not price.empty:
        price = transform_dataframe(price)

    if not df_1.empty:
        df_1 = transform_dataframe(df_1)

    return price, df_1


# Call the load_data function
price, df_1 = load_data()