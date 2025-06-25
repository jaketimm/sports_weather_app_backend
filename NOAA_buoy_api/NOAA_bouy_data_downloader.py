import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import config

class BuoyDataDownloader:
    def __init__(self):
        """Initialize the downloader with configuration."""
        self.config = config
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create directories if they don't exist."""
        data_dir = Path(self.config.FILE_PATHS['data_dir'])
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_units(self, df):
        """Convert units based on configuration."""
        df_converted = df.copy()
        conversions = self.config.CONVERSIONS
        missing_val = self.config.SETTINGS['missing_value_placeholder']
        
        # Convert wind speed from m/s to mph
        if 'WSPD' in df_converted.columns and conversions.get('convert_wspd_to_mph', False):
            df_converted['WSPD'] = df_converted['WSPD'].apply(
                lambda x: round(x * 2.237, 1) if pd.notna(x) else missing_val
            )
        
        # Convert wave height from meters to feet
        if 'WVHT' in df_converted.columns and conversions.get('convert_wvht_to_feet', False):
            df_converted['WVHT'] = df_converted['WVHT'].apply(
                lambda x: round(x * 3.281, 1) if pd.notna(x) else missing_val
            )
        
        # Convert air temperature from Celsius to Fahrenheit
        if 'ATMP' in df_converted.columns and conversions.get('convert_atmp_to_fahrenheit', False):
            df_converted['ATMP'] = df_converted['ATMP'].apply(
                lambda x: round(x * 9/5 + 32, 1) if pd.notna(x) else missing_val
            )
        
        # Convert water temperature from Celsius to Fahrenheit
        if 'WTMP' in df_converted.columns and conversions.get('convert_wtmp_to_fahrenheit', False):
            df_converted['WTMP'] = df_converted['WTMP'].apply(
                lambda x: round(x * 9/5 + 32, 1) if pd.notna(x) else missing_val
            )
        
        # Replace any remaining NaN values with missing_val
        for col in df_converted.columns:
            if col not in ['Station_ID', 'datetime']:
                df_converted[col] = df_converted[col].fillna(missing_val)
        
        return df_converted
    
    def download_and_process_data(self, hour=None):
        """
        Download NDBC buoy data and process it into a DataFrame.
        
        Args:
            hour (str, optional): Specific hour to download. If None, uses current hour.
        
        Returns:
            pandas.DataFrame: Processed buoy data
        """
        
        # Get hour to download
        if hour is None:
            current_hour = datetime.now().strftime("%H")
        else:
            current_hour = f"{int(hour):02d}"
        
        url = f"https://www.ndbc.noaa.gov/data/hourly2/hour_{current_hour}.txt"
        
        # Generate file paths
        raw_filename = self.config.FILE_PATHS['raw_filename_template'].format(hour=current_hour)
        processed_filename = self.config.FILE_PATHS['processed_filename_template'].format(hour=current_hour)
        
        raw_filepath = Path(self.config.FILE_PATHS['data_dir']) / raw_filename
        processed_filepath = Path(self.config.FILE_PATHS['data_dir']) / processed_filename
        
        try:
            print(f"Downloading data from: {url}")
            
            # Download the data
            timeout = self.config.SETTINGS.get('request_timeout', 30)
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
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
            print(f"Saving raw data to: {raw_filepath}")
            with open(raw_filepath, 'w') as f:
                for i, line in enumerate(lines):
                    # Skip the second comment line (index 1)
                    if i == 1 and line.startswith('#'):
                        continue
                    f.write(line + '\n')
            
            # Process the data into DataFrame
            df = self.process_raw_data(lines)
            
            if df.empty:
                print("No data found for the specified buoy IDs at the top of the hour")
                return df
            
            # Convert units
            df_converted = self.convert_units(df)
            
            # Save processed data
            print(f"Saving processed data to: {processed_filepath}")
            df_converted.to_csv(processed_filepath, index=False)
            
            print(f"Successfully processed data for {len(df_converted)} records")
            print(f"Buoy IDs found: {df_converted['Station_ID'].unique().tolist()}")
            
            return df_converted
            
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
    
    def process_raw_data(self, lines):
        """Process raw data lines into a DataFrame."""
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
        enabled_ids = [str(bid) for bid in self.config.ENABLED_BUOYS]
        df_filtered = df[df['STN'].isin(enabled_ids)].copy()
        
        if df_filtered.empty:
            print(f"Warning: No data found for the specified buoy IDs: {enabled_ids}")
            return pd.DataFrame()
        
        # Filter for top of hour only if configured
        if self.config.SETTINGS.get('only_top_of_hour', True):
            df_filtered = df_filtered[df_filtered['mm'] == '00'].copy()
            
            if df_filtered.empty:
                print(f"Warning: No data found at the top of the hour for the specified buoy IDs")
                return pd.DataFrame()
        
        # Create datetime column
        df_filtered['datetime'] = pd.to_datetime(
            df_filtered['YY'] + '-' + df_filtered['MM'] + '-' + df_filtered['DD'] + ' ' + 
            df_filtered['hh'] + ':' + df_filtered['mm'],
            format='%Y-%m-%d %H:%M'
        )
        
        # Rename STN to Station_ID
        df_filtered['Station_ID'] = df_filtered['STN']
        
        # Check if all required fields exist
        missing_fields = [field for field in self.config.ENABLED_FIELDS 
                         if field not in df_filtered.columns]
        if missing_fields:
            print(f"Warning: Missing fields in data: {missing_fields}")
        
        # Keep only available columns
        available_cols = ['Station_ID', 'datetime'] + [
            field for field in self.config.ENABLED_FIELDS 
            if field in df_filtered.columns
        ]
        
        result_df = df_filtered[available_cols].copy()
        
        # Convert numeric columns, replacing 'MM' with NaN for now (will be replaced with N/A after conversion)
        missing_val = self.config.SETTINGS['missing_value_placeholder']
        numeric_cols = [col for col in available_cols if col not in ['Station_ID', 'datetime']]
        
        for col in numeric_cols:
            # First replace 'MM' with NaN for conversion
            result_df[col] = pd.to_numeric(result_df[col].replace('MM', pd.NA), errors='coerce')
        
        # Reset index
        result_df.reset_index(drop=True, inplace=True)
        
        return result_df

def main():
    """Main function to run the buoy data downloader."""
    
    # Initialize downloader
    downloader = BuoyDataDownloader()
    
    # Download and process current hour data
    buoy_df = downloader.download_and_process_data()
    
    # Display results
    if not buoy_df.empty:
        print("\nProcessed Data:")
    else:
        print("No data was successfully processed.")

if __name__ == "__main__":
    main()