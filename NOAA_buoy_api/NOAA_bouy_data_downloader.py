import requests
import pandas as pd
from datetime import datetime
import os
import sys

def download_and_process_buoy_data(enabled_ids, output_file=None):
    """
    Download NDBC buoy data for the current hour and process it into a DataFrame.
    
    Args:
        enabled_ids (list): List of buoy IDs to extract
        output_file (str, optional): Path to save the raw data file
    
    Returns:
        pandas.DataFrame: Processed buoy data
    """
    
    # Get current hour in 24-hour format
    current_hour = datetime.now().strftime("%H")
    url = f"https://www.ndbc.noaa.gov/data/hourly2/hour_{current_hour}.txt"
    
    # Set default output file if not provided
    if output_file is None:
        output_file = f"buoy_data_hour_{current_hour}.txt"
    
    try:
        print(f"Downloading data from: {url}")
        
        # Download the data
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Check if response is empty
        if not response.text.strip():
            raise ValueError("Downloaded file is empty")
        
        # Split into lines
        lines = response.text.strip().split('\n')
        
        # Check if file only contains comments
        data_lines = [line for line in lines if not line.startswith('#')]
        if not data_lines:
            raise ValueError("Downloaded file contains only comments or headers")
        
        # Save raw data to file, skipping the second comment row
        print(f"Saving raw data to: {output_file}")
        with open(output_file, 'w') as f:
            for i, line in enumerate(lines):
                # Skip the second comment line (index 1)
                if i == 1 and line.startswith('#'):
                    continue
                f.write(line + '\n')
        
        # Process the data into DataFrame
        # Find the first comment line (header) and data lines
        header_line = None
        data_start_idx = 0
        
        for i, line in enumerate(lines):
            if line.startswith('#STN'):
                header_line = line
            elif not line.startswith('#'):
                data_start_idx = i
                break
        
        if header_line is None:
            raise ValueError("Could not find header line in data")
        
        # Extract column names from header (remove # and split)
        columns = header_line[1:].split()
        
        # Read data lines
        data_rows = []
        for line in lines[data_start_idx:]:
            if line.strip() and not line.startswith('#'):
                data_rows.append(line.split())
        
        if not data_rows:
            raise ValueError("No data rows found")
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=columns)
        
        # Filter for enabled IDs
        df_filtered = df[df['STN'].isin(map(str, enabled_ids))].copy()
        
        if df_filtered.empty:
            print(f"Warning: No data found for the specified buoy IDs: {enabled_ids}")
            return pd.DataFrame()
        
        # Create datetime column
        df_filtered['datetime'] = pd.to_datetime(
            df_filtered['YY'] + '-' + df_filtered['MM'] + '-' + df_filtered['DD'] + ' ' + 
            df_filtered['hh'] + ':' + df_filtered['mm'],
            format='%Y-%m-%d %H:%M'
        )
        
        # Select and rename desired columns
        columns_to_keep = ['datetime', 'WDIR', 'WSPD', 'ATMP', 'WVHT', 'WTMP']
        
        # Check if all required columns exist
        missing_cols = [col for col in columns_to_keep if col not in df_filtered.columns and col != 'datetime']
        if missing_cols:
            print(f"Warning: Missing columns in data: {missing_cols}")
        
        # Keep only available columns
        available_cols = ['datetime'] + [col for col in columns_to_keep[1:] if col in df_filtered.columns]
        result_df = df_filtered[available_cols].copy()
        
        # Convert numeric columns to float, replacing 'MM' with NaN
        numeric_cols = [col for col in available_cols if col != 'datetime']
        for col in numeric_cols:
            result_df[col] = pd.to_numeric(result_df[col].replace('MM', pd.NA), errors='coerce')
        
        # Reset index
        result_df.reset_index(drop=True, inplace=True)
        
        print(f"Successfully processed data for {len(result_df)} records")
        print(f"Buoy IDs found: {result_df['WDIR'].index if 'STN' in df_filtered.columns else 'N/A'}")
        
        return result_df
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()
    
    except requests.exceptions.Timeout:
        print("Request timed out. The server may be slow to respond.")
        return pd.DataFrame()
    
    except ValueError as e:
        print(f"Data processing error: {e}")
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    # List of buoy IDs you want to extract
    enabled_buoy_ids = ['13001', '13002', '13008']  # Add your desired buoy IDs here
    
    # Download and process the data
    buoy_df = download_and_process_buoy_data(
        enabled_ids=enabled_buoy_ids,
        output_file="current_hour_buoy_data.txt"
    )
    
    # Display results
    if not buoy_df.empty:
        print("\nProcessed Data:")
        print(buoy_df.to_string(index=False))
        
        # Optionally save processed data to CSV
        csv_filename = f"processed_buoy_data_hour_{datetime.now().strftime('%H')}.csv"
        buoy_df.to_csv(csv_filename, index=False)
        print(f"\nProcessed data saved to: {csv_filename}")
    else:
        print("No data was successfully processed.")