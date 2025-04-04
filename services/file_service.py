import os
import pandas as pd
from config import logger, UPLOAD_FOLDER
from utils.date_utils import parse_dates_with_format_detection

def detect_file_format(file_path):
    """
    Detect the format of the CSV file (Google Ads, Meta, or other) and return appropriate parsing parameters.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        dict: Dictionary with parsing parameters (skiprows, encoding, etc.)
    """
    # Try different skiprows values to determine the best option
    best_format = {
        'skiprows': 0, 
        'source': 'unknown',
        'date_columns': []
    }
    
    # First try with no skipped rows to see what's there
    try:
        df_sample = pd.read_csv(file_path, nrows=5)
        column_names = df_sample.columns.tolist()
        
        # Look for Google Ads format indicators
        if ('Campaign' in column_names and 'Day' in column_names):
            # This might be a Google Ads file with no header rows
            best_format['source'] = 'google_ads'
            best_format['skiprows'] = 0
            best_format['date_columns'] = ['Day']
            logger.info("Detected Google Ads format with no header rows")
            return best_format
            
        # Look for Meta format indicators
        if any('reporting' in col.lower() for col in column_names):
            best_format['source'] = 'meta'
            best_format['skiprows'] = 0
            # Find date columns
            best_format['date_columns'] = [col for col in column_names if 
                                          any(term in col.lower() for term in 
                                             ['reporting', 'date', 'day', 'starts', 'ends'])]
            logger.info(f"Detected Meta format. Date columns: {best_format['date_columns']}")
            return best_format
            
    except Exception as e:
        logger.warning(f"Error reading file with no skipped rows: {e}")
        
    # Try with 1 or 2 skipped rows (common for Google Ads)
    for skip_rows in [1, 2, 3]:
        try:
            df_sample = pd.read_csv(file_path, skiprows=skip_rows, nrows=5)
            column_names = df_sample.columns.tolist()
            
            # Look for Google Ads format indicators after skipping rows
            if ('Campaign' in column_names and 'Day' in column_names):
                best_format['source'] = 'google_ads'
                best_format['skiprows'] = skip_rows
                best_format['date_columns'] = ['Day']
                logger.info(f"Detected Google Ads format with {skip_rows} header rows")
                return best_format
        
        except Exception as e:
            logger.warning(f"Error reading file with skiprows={skip_rows}: {e}")
    
    # If we can't determine a specific format, use default with smart column detection
    logger.info("Could not determine specific file format, using generic parsing")
    return best_format

def process_uploaded_file(file_path):
    """
    Process an uploaded CSV file to identify date and numeric columns.
    
    Args:
        file_path: Path to the uploaded CSV file
        
    Returns:
        tuple: (DataFrame, date_columns, numeric_columns, detected_date_format)
    """
    # Detect file format and get appropriate parsing parameters
    file_format = detect_file_format(file_path)
    logger.info(f"Detected file format: {file_format}")
    
    # Read CSV file with detected parameters
    df = pd.read_csv(file_path, skiprows=file_format['skiprows'])
    logger.info(f"Read CSV with skiprows={file_format['skiprows']}. Columns: {df.columns.tolist()}")
    
    # Make sure date columns are properly formatted
    detected_date_format = 'auto'
    date_cols = []
    
    # First, create a list of potential date columns in their original order
    date_candidates = []
    
    # Add suggested date columns from format detection
    if file_format['date_columns']:
        for col in file_format['date_columns']:
            if col in df.columns and col not in date_candidates:
                date_candidates.append(col)
    
    # Add columns with date-related terms in their names
    for col in df.columns:
        if col not in date_candidates:
            col_lower = col.lower()
            if any(term in col_lower for term in ['date', 'day', 'time', 'report', 'start', 
                                                 'end', 'period', 'month', 'year']):
                date_candidates.append(col)
    
    # Add all string columns that might contain dates
    for col in df.columns:
        if col not in date_candidates and df[col].dtype == 'object':
            # Check if column might contain dates (simple check for / or - or .)
            sample_vals = df[col].dropna().astype(str).head(3)
            if any(('/' in str(val) or '-' in str(val) or '.' in str(val)) for val in sample_vals):
                date_candidates.append(col)
    
    # Now check each candidate in order and use the first valid date column
    for col in date_candidates:
        try:
            parsed_dates, format_detected = parse_dates_with_format_detection(df, col)
            if not parsed_dates.isna().all():
                df[col] = parsed_dates
                date_cols = [col]  # We only use the first valid date column
                detected_date_format = format_detected
                logger.info(f"Using first valid date column: {col} with format {format_detected}")
                break  # Stop after finding the first valid date column
        except Exception as e:
            logger.warning(f"Error parsing dates in column {col}: {e}")
    
    # If still no date columns found, try all columns as a last resort
    if not date_cols:
        for col in df.columns:
            if col not in date_candidates:
                try:
                    parsed_dates, format_detected = parse_dates_with_format_detection(df, col)
                    if not parsed_dates.isna().all():
                        df[col] = parsed_dates
                        date_cols = [col]
                        detected_date_format = format_detected
                        logger.info(f"Found date column: {col} with format {format_detected}")
                        break
                except Exception as e:
                    continue
    
    # Handle numeric columns with commas in the values (e.g., "1,476.69")
    for col in df.columns:
        if col not in date_cols and df[col].dtype == 'object':
            try:
                # Remove commas and convert to numeric
                df[col] = df[col].astype(str).str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.info(f"Converted column {col} to numeric")
            except Exception as e:
                logger.warning(f"Could not convert column {col} to numeric: {e}")
    
    # Get all numeric columns
    all_numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Define accepted marketing metrics keywords
    marketing_metrics = [
        'clicks', 'link clicks', 'total clicks',
        'conversions', 'all conv', 'conv', 'website purchases',
        'conversion rate', 'conv. rate', 'cr', 'cvr',
        'impressions', 'impr', 'imps',
        'cpc', 'cost per click', 'avg. cpc', 'average cpc',
        'ctr', 'click through rate', 'click-through rate',
        'cpm', 'cost per mille', 'cost per thousand',
        'spend', 'cost', 'amount spent', 'value', 'conv. value'
    ]
    
    # Filter numeric columns to only include marketing metrics
    numeric_cols = []
    for col in all_numeric_cols:
        col_lower = col.lower()
        if any(metric in col_lower for metric in marketing_metrics):
            numeric_cols.append(col)
    
    # If no marketing metrics were found, fall back to all numeric columns
    if not numeric_cols:
        logger.warning("No standard marketing metrics found, using all numeric columns")
        numeric_cols = all_numeric_cols
    
    logger.info(f"Marketing metric columns: {numeric_cols}")
    
    return df, date_cols, numeric_cols, detected_date_format, file_format

def prepare_data_for_forecast(file_path, file_format, date_col, date_format, selected_metrics):
    """
    Prepare data for forecasting by loading the file and formatting columns.
    
    Args:
        file_path: Path to the CSV file
        file_format: Dictionary with file format information
        date_col: Name of the date column
        date_format: Format string for date parsing
        selected_metrics: List of metrics to forecast
        
    Returns:
        DataFrame with formatted data ready for forecasting
    """
    # Read the CSV file with appropriate parameters
    df = pd.read_csv(file_path, skiprows=file_format['skiprows'])
    
    # Convert date column to datetime using the selected format
    from utils.date_utils import convert_column_to_datetime
    df = convert_column_to_datetime(df, date_col, date_format)
    
    # Clean numeric data - remove commas from numbers
    for col in selected_metrics:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_budget_data(df, file_format):
    """
    Calculate daily average spend based on the CSV data.
    
    Args:
        df: DataFrame containing the data
        file_format: Dictionary with detected file format info
        
    Returns:
        dict: Dictionary with budget data including daily average and currency
    """
    import pandas as pd
    from config import logger
    
    budget_data = {
        'dailyAverage': 0,
        'currency': '£'  # Default currency
    }
    
    # Identify spending columns based on file source
    spend_columns = []
    
    if file_format['source'] == 'google_ads':
        # For Google Ads, look for cost columns
        potential_columns = ['Cost', 'All conv. value', 'Cost / conv.']
        spend_columns = [col for col in potential_columns if col in df.columns]
        
        # If specific columns aren't found, look for columns containing 'cost'
        if not spend_columns:
            spend_columns = [col for col in df.columns if 'cost' in col.lower()]
            
    elif file_format['source'] == 'meta':
        # For Meta, look for spend columns
        potential_columns = ['Amount spent', 'Amount spent (EUR)', 'Spend', 'Cost per result']
        spend_columns = [col for col in potential_columns if col in df.columns]
        
        # If specific columns aren't found, look for columns containing 'spend' or 'cost'
        if not spend_columns:
            spend_columns = [col for col in df.columns if any(term in col.lower() for term in ['spend', 'cost', 'amount'])]
    
    # For unknown formats, look for general spending keywords
    if not spend_columns:
        spend_keywords = ['spend', 'cost', 'budget', 'amount']
        spend_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in spend_keywords)]
    
    logger.info(f"Identified spend columns: {spend_columns}")
    
    # Find currency symbol if available
    for col in spend_columns:
        # Check if column name contains currency indicators
        col_lower = col.lower()
        if 'eur' in col_lower or '€' in col_lower:
            budget_data['currency'] = '€'
            break
        elif 'usd' in col_lower or '$' in col_lower:
            budget_data['currency'] = '$'
            break
        elif 'gbp' in col_lower or '£' in col_lower:
            budget_data['currency'] = '£'
            break
    
    # Calculate daily average spend
    if spend_columns:
        primary_spend_column = spend_columns[0]  # Use the first identified spending column
        logger.info(f"Using {primary_spend_column} as the primary spending column for budget calculation")
        
        # Convert to numeric if needed
        if df[primary_spend_column].dtype == 'object':
            df[primary_spend_column] = df[primary_spend_column].astype(str).str.replace(',', '')
            df[primary_spend_column] = pd.to_numeric(df[primary_spend_column], errors='coerce')
        
        # Calculate the daily average
        total_spend = df[primary_spend_column].sum()
        date_col = file_format['date_columns'][0] if file_format['date_columns'] else None
        
        if date_col and date_col in df.columns:
            # Count unique dates to determine number of days
            num_days = df[date_col].nunique()
            logger.info(f"Found {num_days} unique days in data")
        else:
            # If no date column found, use row count as fallback
            num_days = len(df)
            logger.info(f"Using row count ({num_days}) as number of days")
        
        if num_days > 0:
            budget_data['dailyAverage'] = float(total_spend / num_days)
            logger.info(f"Calculated daily average spend: {budget_data['dailyAverage']} {budget_data['currency']}")
        else:
            logger.warning("Could not calculate daily average spend: no days found in data")
    else:
        logger.warning("No spending columns identified in the CSV")
    
    return budget_data