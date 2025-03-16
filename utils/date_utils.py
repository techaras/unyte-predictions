import pandas as pd
from config import logger

def parse_dates_with_format_detection(df, date_col):
    """Try to detect date format and parse dates accordingly.
    
    Args:
        df: DataFrame containing date column
        date_col: Name of the column containing dates
        
    Returns:
        tuple: (parsed_dates, detected_format)
    """
    # If column contains strings that look like two dates separated by space/newline
    if df[date_col].dtype == 'object':
        sample_vals = df[date_col].dropna().astype(str).head()
        # Check if values contain multiple dates (common in Meta exports)
        if any(' ' in str(val) for val in sample_vals):
            logger.info(f"Column {date_col} may contain multiple dates - trying to extract first date")
            # Extract first date from each value (before the space)
            df[date_col] = df[date_col].astype(str).str.split(' ').str[0]
            
    # First try automatic parsing
    dates_auto = pd.to_datetime(df[date_col], errors='coerce')
    
    # Try explicit formats
    dates_mdy = pd.to_datetime(df[date_col], format='%m/%d/%Y', errors='coerce')
    dates_dmy = pd.to_datetime(df[date_col], format='%d/%m/%Y', errors='coerce')
    
    # Try additional European format (with dots)
    dates_dmy_dot = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='coerce')
    
    # Count valid dates for each method
    valid_auto = (~dates_auto.isna()).sum()
    valid_mdy = (~dates_mdy.isna()).sum()
    valid_dmy = (~dates_dmy.isna()).sum()
    valid_dmy_dot = (~dates_dmy_dot.isna()).sum()
    
    # Choose the format that successfully parsed the most dates
    if valid_mdy >= valid_auto and valid_mdy >= valid_dmy and valid_mdy >= valid_dmy_dot:
        logger.info(f"Detected American date format (MM/DD/YYYY) for column {date_col}")
        return dates_mdy, '%m/%d/%Y'
    elif valid_dmy >= valid_auto and valid_dmy >= valid_dmy_dot:
        logger.info(f"Detected European date format (DD/MM/YYYY) for column {date_col}")
        return dates_dmy, '%d/%m/%Y'
    elif valid_dmy_dot >= valid_auto:
        logger.info(f"Detected European date format with dots (DD.MM.YYYY) for column {date_col}")
        return dates_dmy_dot, '%d.%m.%Y'
    else:
        logger.info(f"Using auto-detected date format for column {date_col}")
        return dates_auto, 'auto'

def convert_column_to_datetime(df, date_col, date_format='auto'):
    """Convert a column to datetime using the specified format.
    
    Args:
        df: DataFrame containing the date column
        date_col: Name of the column to convert
        date_format: Format string to use for conversion
        
    Returns:
        DataFrame with converted column
    """
    if date_format == 'auto':
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        logger.info(f"Using automatic date parsing for column {date_col}")
    else:
        df[date_col] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
        logger.info(f"Using format {date_format} for column {date_col}")
    
    return df