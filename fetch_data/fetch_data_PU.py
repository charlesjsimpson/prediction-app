import os
import pandas as pd
from pathlib import Path

# Define the directory containing the files
project_root = Path(__file__).parent.parent
data_root = os.path.join(project_root, 'data')

# List of main files to process
file_names = ["2023_PU.xlsx", "2024_PU.xlsx", "2025_PU_03_13.xlsx"]

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

    # Keep only the necessary columns
    df = df[['day', 'type', 'sous_type', 'n_rooms', 'n_customers', 'ca_room', 'pm', 'Source_File']]

    # Add a column with the year
    df['year'] = pd.to_datetime(df['day'], errors='coerce').dt.year

    # Add a column with the month number (1-12)
    df['month'] = pd.to_datetime(df['day'], errors='coerce').dt.month
    
    # Add a column with the month name
    df['month_name'] = pd.to_datetime(df['day'], errors='coerce').dt.month_name()

    # Add a column with the year-month
    df['year_month'] = pd.to_datetime(df['day'], errors='coerce').dt.to_period('M').astype(str)

    # Add a column with the day of the week
    df['day_of_week'] = pd.to_datetime(df['day'], errors='coerce').dt.day_name()

    return df

# Function to load data
def load_data():
    dataframe_list = []

    # Iterate through each main file and load it into a DataFrame
    for file_name in file_names:
        file_path = os.path.join(data_root, file_name)
        if os.path.exists(file_path):
            df = pd.read_excel(
                file_path,
                sheet_name=0,       # Read the first sheet
                skiprows=1,         # Skip the first row
                engine="openpyxl"   # Use the openpyxl engine
            )
            df['Source_File'] = file_name  # Add a column indicating the source file
            dataframe_list.append(df)  # Add the DataFrame to the list

    # Aggregate all main DataFrames into one
    price = pd.concat(dataframe_list, ignore_index=True)

    # Load the separate file
    separate_file_path = os.path.join(data_root, separate_file)
    if os.path.exists(separate_file_path):
        df_1 = pd.read_excel(
            separate_file_path,
            sheet_name=0,       # Read the first sheet
            skiprows=1,         # Skip the first row
            engine="openpyxl"   # Use the openpyxl engine
        )
        df_1['Source_File'] = separate_file  # Add a column indicating the source file
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