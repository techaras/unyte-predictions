import pandas as pd
import numpy as np
from config import logger
from services.file_service import detect_file_format
from datetime import datetime, timedelta
import json
import csv

def process_impact_files(uploaded_files):
    """
    Process multiple uploaded files for impact analysis.
    
    Args:
        uploaded_files: List of dictionaries with file information
        
    Returns:
        dict: Processed impact data
    """
    impact_data = {
        'forecasts': []
    }
    
    for index, file_info in enumerate(uploaded_files):
        try:
            file_path = file_info['path']
            logger.info(f"Processing file: {file_info['original_name']}")
            
            # First, check if this is a forecast CSV format (with metadata at the top)
            is_forecast_csv, metadata, data_df = parse_forecast_csv(file_path)
            
            # Initialize budget data with defaults
            budget_value = None
            budget_currency = '£'  # Changed from '€' to '£'
            
            if is_forecast_csv:
                # Extract budget information from metadata
                if 'budget' in metadata:
                    budget_value = float(metadata.get('budget', 0))
                if 'currency' in metadata:
                    budget_currency = metadata.get('currency', '€')
                
                # Extract information from the parsed metadata and data
                forecast_id = f"ForecastName {index + 1}"
                forecast_title = metadata.get('forecast_title', forecast_id)
                platform = metadata.get('platform', 'Unknown')
                campaign = extract_campaign_name_from_metadata(metadata, file_info['original_name'])
                
                # Extract ALL metrics from the data portion
                metrics = extract_all_metrics_from_forecast_data(data_df)
                
                # Extract date range from metadata
                start_date = datetime.now().strftime('%Y-%m-%d')
                forecast_days = 90  # Default to 90 days forecast
                end_date = (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
                
                # Try to get date range from metadata
                if 'start_date' in metadata:
                    start_date = metadata.get('start_date', start_date)
                if 'end_date' in metadata:
                    end_date = metadata.get('end_date', end_date)
                
                logger.info(f"Successfully parsed forecast CSV: {forecast_title}, Platform: {platform}")
            else:
                # Fall back to regular CSV parsing
                logger.info(f"Not a forecast CSV, trying standard parsing")
                
                # Detect file format
                file_format = detect_file_format(file_path)
                
                # Read CSV with pandas directly - with more flexible parsing
                df = pd.read_csv(file_path, skiprows=file_format['skiprows'], delimiter=',', 
                                 engine='python', error_bad_lines=False)
                
                # Extract platform from file content or name
                platform = determine_platform(df, file_info['original_name'], file_format)
                
                # Extract campaign name if available
                campaign = extract_campaign_name(df, file_info['original_name'])
                
                # Extract ALL metrics
                metrics = extract_all_metrics(df)
                
                # Try to find budget data in the file
                try:
                    # Look for columns with budget/cost keywords
                    cost_cols = [col for col in df.columns if any(term in col.lower() for term in 
                                ['budget', 'cost', 'spend', 'amount'])]
                    
                    if cost_cols:
                        # Use the first cost column found
                        total_cost = df[cost_cols[0]].sum()
                        budget_value = float(total_cost)
                        
                        # Try to detect currency from column name
                        # if any(currency in cost_cols[0].lower() for currency in ['eur', '€']):
                        #     budget_currency = '€'
                        # elif any(currency in cost_cols[0].lower() for currency in ['usd', '$']):
                        #     budget_currency = '$'
                        # elif any(currency in cost_cols[0].lower() for currency in ['gbp', '£']):
                        #     budget_currency = '£'
                except Exception as e:
                    logger.warning(f"Could not extract budget information: {str(e)}")
                
                # Generate forecast ID and title
                forecast_id = f"ForecastName {index + 1}"
                forecast_title = forecast_id
                
                # Set default date range
                start_date = datetime.now().strftime('%Y-%m-%d')
                forecast_days = 90  # Default to 90 days forecast
                end_date = (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
                
                # Try to extract date range from data
                if file_format['date_columns'] and not df.empty:
                    # If this is a regular CSV, try to extract dates from the data
                    date_col = file_format['date_columns'][0]
                    if date_col in df.columns:
                        # Get date range
                        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        last_date = df[date_col].max()
                        if pd.notna(last_date):
                            start_date = last_date.strftime('%Y-%m-%d')
                            end_date = (last_date + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
            
            # Calculate days between start and end date
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                forecast_days = (end_dt - start_dt).days
            except:
                forecast_days = 90  # Fallback if date parsing fails
            
            # Create forecast entry
            forecast_entry = {
                'id': forecast_id,
                'title': forecast_title,
                'platform': platform,
                'campaign': campaign,
                'metrics': metrics,
                'date_range': {
                    'start': start_date,
                    'end': end_date,
                    'days': forecast_days
                },
                # Add budget information to the forecast entry
                'budget': {
                    'value': budget_value,
                    'currency': budget_currency
                }
            }
            
            impact_data['forecasts'].append(forecast_entry)
            
        except Exception as e:
            logger.error(f"Error processing file {file_info['original_name']}: {str(e)}")
            # Continue processing other files
    
    # Initialize metrics
    for forecast in impact_data['forecasts']:
        for metric in forecast['metrics']:
            metric['simulated'] = metric['current']
            metric['impact'] = 0.0
    
    # Extract overall date range (using the first forecast's range as default)
    if impact_data['forecasts']:
        first_forecast = impact_data['forecasts'][0]
        if 'date_range' in first_forecast:
            impact_data['date_range'] = first_forecast['date_range']
        else:
            # Fallback date range
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
            impact_data['date_range'] = {
                'start': start_date,
                'end': end_date,
                'days': 90
            }
    
    logger.info(f"Processed {len(impact_data['forecasts'])} forecasts")
    return impact_data

def parse_forecast_csv(file_path):
    """
    Parse a CSV file in the forecast export format (with metadata headers).
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        tuple: (is_forecast_csv, metadata_dict, data_dataframe)
    """
    try:
        # Read the first 10 lines to check format
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()[:10]]
        
        # Check if it follows the metadata format with key-value pairs
        if len(lines) >= 2 and ',' in lines[0] and len(lines[0].split(',')) == 2:
            # Count how many metadata rows we have
            metadata_rows = 0
            metadata = {}
            
            # Extract metadata
            for line in lines:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    key, value = parts
                    if value.strip():  # Only store non-empty values
                        metadata[key.lower().strip()] = value.strip()
                    metadata_rows += 1
                else:
                    # Stop when we hit a line that doesn't look like metadata
                    break
            
            # Check if we have standard metadata keys
            standard_keys = ['forecast_title', 'platform', 'currency']
            found_keys = [key for key in standard_keys if key in metadata]
            
            if len(found_keys) >= 2:  # If we found at least 2 standard keys, it's our format
                # Find the data table headers
                data_start_row = 0
                for i, line in enumerate(lines):
                    if 'date' in line.lower() and 'metric_type' in line.lower():
                        data_start_row = i
                        break
                
                if data_start_row == 0 and metadata_rows > 0:
                    # If we didn't find the data headers but had metadata, start after metadata
                    data_start_row = metadata_rows
                
                # Read the data portion
                try:
                    data_df = pd.read_csv(file_path, skiprows=data_start_row)
                    return True, metadata, data_df
                except Exception as e:
                    logger.warning(f"Failed to read data portion of forecast CSV: {str(e)}")
        
        # If we got here, it's not a forecast CSV or we couldn't parse it
        return False, {}, None
    
    except Exception as e:
        logger.warning(f"Failed to parse as forecast CSV: {str(e)}")
        return False, {}, None

def extract_campaign_name_from_metadata(metadata, filename):
    """
    Extract campaign name from metadata or fallback to filename.
    
    Args:
        metadata: Dictionary of metadata from forecast CSV
        filename: Original filename
        
    Returns:
        str: Campaign name
    """
    # Try to extract from title first
    if 'forecast_title' in metadata:
        title = metadata['forecast_title']
        # Check if title contains campaign indicators
        campaign_indicators = ['campaign', 'Campaign', 'Madrid', 'madrid', 'Performance']
        for indicator in campaign_indicators:
            if indicator in title:
                parts = title.split(' - ')
                # Return the part that contains the campaign indicator
                for part in parts:
                    if any(indicator in part for indicator in campaign_indicators):
                        return part.strip()
                # Or just return the whole title
                return title
    
    # Try to extract from filename if no campaign in title
    name = filename.rsplit('.', 1)[0]
    for prefix in ['report_', 'export_', 'data_', 'campaign_']:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
    
    # Check if name contains specific campaign terminology
    if any(term in name for term in ['Madrid', 'madrid', 'Performance']):
        return 'Madrid Performance'
    
    # If name is too generic, check platform and make a sensible default
    if 'platform' in metadata:
        platform = metadata['platform']
        if platform.lower() in ['meta', 'facebook']:
            return 'Meta Awareness'
        elif platform.lower() in ['google', 'google ads']:
            return 'Google Performance'
        elif platform.lower() in ['amazon']:
            return 'Amazon Sponsored'
    
    # Default if nothing else works
    return 'All Campaigns'

def extract_all_metrics_from_forecast_data(df):
    """
    Extract ALL numeric metrics from forecast data dataframe using aggregates.
    
    Args:
        df: DataFrame containing forecast data
        
    Returns:
        list: List of metric dictionaries
    """
    metrics = []
    
    # Skip these columns as they're not metrics
    non_metric_columns = ['date', 'metric_type', 'date_range', 'segment', 'campaign']
    
    # First pass: Get all columns that could be metrics
    potential_metric_columns = [col for col in df.columns 
                              if col.lower() not in non_metric_columns]
    
    # Second pass: Calculate raw totals
    raw_totals = {}
    for col in potential_metric_columns:
        try:
            numeric_values = pd.to_numeric(df[col], errors='coerce')
            if numeric_values.notna().sum() > len(df) * 0.5:  # If >50% are numeric
                raw_totals[col] = numeric_values.sum()
        except:
            continue
    
    # Third pass: Process metrics based on their type
    for col in raw_totals.keys():
        try:
            # Use original column name instead of formatting it
            display_name = col
            metric_lower = col.lower()
            
            value = raw_totals[col]
            
            # Special handling for derived metrics (similar to extract_all_metrics function)
            if 'ctr' in metric_lower or 'click through rate' in metric_lower:
                # Similar CTR calculation as in extract_all_metrics
                clicks_col = next((c for c in raw_totals if 'click' in c.lower()), None)
                impr_col = next((c for c in raw_totals if 'impr' in c.lower() or 'impression' in c.lower()), None)
                
                if clicks_col and impr_col and raw_totals[impr_col] > 0:
                    value = (raw_totals[clicks_col] / raw_totals[impr_col]) * 100
            
            # Add similar blocks for other rate metrics as in extract_all_metrics
            
            # Format the value appropriately
            formatted_value = format_metric_value(display_name, value)
            
            metrics.append({
                'name': display_name,
                'current': formatted_value,
                'simulated': formatted_value,
                'impact': 0.0
            })
        except Exception as e:
            logger.warning(f"Error processing metric column {col}: {str(e)}")
    
    # If no metrics were extracted, provide the standard three as fallback
    if not metrics:
        metrics = generate_default_metrics()
    
    return metrics

def extract_all_metrics(df):
    """
    Extract ALL numeric metrics from the dataframe using aggregate totals.
    Properly handles different metric types (counts, rates, financial metrics).
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        list: List of metric dictionaries
    """
    metrics = []
    
    # Skip these columns as they're not metrics
    non_metric_columns = ['date', 'campaign', 'ad_group', 'ad', 'keyword', 'platform', 
                        'source', 'medium', 'device', 'country', 'region', 'city']
    
    # First pass: Identify all possible metric columns
    potential_metric_columns = []
    for col in df.columns:
        if col.lower() in [c.lower() for c in non_metric_columns]:
            continue
            
        # Check if column contains primarily numeric data
        try:
            numeric_values = pd.to_numeric(df[col], errors='coerce')
            if numeric_values.notna().sum() > len(df) * 0.5:  # If >50% are numeric
                potential_metric_columns.append(col)
        except:
            continue
    
    # Second pass: Calculate raw totals for all metrics and store
    raw_totals = {}
    for col in potential_metric_columns:
        try:
            values = pd.to_numeric(df[col], errors='coerce')
            raw_totals[col] = values.sum()
        except Exception as e:
            logger.warning(f"Error calculating raw total for {col}: {str(e)}")
    
    # Third pass: Process each metric with proper logic based on metric type
    for col in potential_metric_columns:
        try:
            # Use original column name instead of formatting it
            metric_name = col
            metric_lower = col.lower()
            
            # Skip if raw total is NaN or too small
            if pd.isna(raw_totals[col]) or abs(raw_totals[col]) < 0.00001:
                continue
            
            # Default to using the raw total
            value = raw_totals[col]
            
            # Special handling for derived metrics
            if 'ctr' in metric_lower or 'click through rate' in metric_lower:
                # If we have both clicks and impressions, recalculate CTR from totals
                clicks_col = next((c for c in raw_totals if 'click' in c.lower()), None)
                impr_col = next((c for c in raw_totals if 'impr' in c.lower() or 'impression' in c.lower()), None)
                
                if clicks_col and impr_col and raw_totals[impr_col] > 0:
                    value = (raw_totals[clicks_col] / raw_totals[impr_col]) * 100
                
            elif 'conversion rate' in metric_lower:
                # Recalculate conversion rate from total conversions and clicks
                conv_col = next((c for c in raw_totals if 'conv' in c.lower() and 'rate' not in c.lower()), None)
                clicks_col = next((c for c in raw_totals if 'click' in c.lower()), None)
                
                if conv_col and clicks_col and raw_totals[clicks_col] > 0:
                    value = (raw_totals[conv_col] / raw_totals[clicks_col]) * 100
            
            elif 'roas' in metric_lower:
                # Recalculate ROAS from conversion value and cost
                value_col = next((c for c in raw_totals if 'value' in c.lower() or 'revenue' in c.lower()), None)
                cost_col = next((c for c in raw_totals if 'cost' in c.lower() or 'spend' in c.lower()), None)
                
                if value_col and cost_col and raw_totals[cost_col] > 0:
                    value = raw_totals[value_col] / raw_totals[cost_col]
            
            elif 'roi' in metric_lower:
                # Recalculate ROI from revenue and cost
                revenue_col = next((c for c in raw_totals if 'revenue' in c.lower() or 'value' in c.lower()), None)
                cost_col = next((c for c in raw_totals if 'cost' in c.lower() or 'spend' in c.lower()), None)
                
                if revenue_col and cost_col and raw_totals[cost_col] > 0:
                    value = ((raw_totals[revenue_col] - raw_totals[cost_col]) / raw_totals[cost_col]) * 100
            
            # Format the value appropriately
            formatted_value = format_metric_value(metric_name, value)
            
            metrics.append({
                'name': metric_name,
                'current': formatted_value,
                'simulated': formatted_value,
                'impact': 0.0
            })
        except Exception as e:
            logger.warning(f"Error processing metric {col}: {str(e)}")
    
    # If no metrics were extracted, provide default ones
    if not metrics:
        metrics = generate_default_metrics()
    
    return metrics

def format_metric_name(column_name):
    """
    Format a column name into a user-friendly metric name.
    
    Args:
        column_name: Original column name
        
    Returns:
        str: Formatted metric name
    """
    # Remove common prefixes/suffixes
    name = column_name.replace('_', ' ').strip()
    
    # Handle special cases
    name_lower = name.lower()
    if 'roas' in name_lower:
        return 'ROAS'
    elif 'ctr' in name_lower and 'ctr' == name_lower:
        return 'CTR'
    elif 'cpm' in name_lower and 'cpm' == name_lower:
        return 'CPM'
    elif 'cpc' in name_lower and 'cpc' == name_lower:
        return 'CPC'
    elif 'cpa' in name_lower and 'cpa' == name_lower:
        return 'CPA'
    elif 'conv' in name_lower and 'rate' in name_lower:
        return 'Conversion Rate'
    elif 'conv' in name_lower and 'value' in name_lower:
        return 'Conversion Value'
    elif any(term in name_lower for term in ['conv', 'conversion', 'purchase']):
        return 'Conversions'
    elif any(term in name_lower for term in ['click', 'clic']):
        return 'Clicks'
    elif 'impr' in name_lower or 'impression' in name_lower:
        return 'Impressions'
    elif 'cost' in name_lower or 'spend' in name_lower:
        return 'Cost'
    elif 'revenue' in name_lower:
        return 'Revenue'
    elif 'roi' in name_lower:
        return 'ROI'
    
    # Capitalize words for other metrics
    words = name.split()
    return ' '.join(word.capitalize() for word in words)

def format_metric_value(metric_name, value):
    """
    Format the metric value appropriately based on metric type.
    
    Args:
        metric_name: Name of the metric
        value: Raw numeric value
        
    Returns:
        Formatted value (could be float or int)
    """
    metric_lower = metric_name.lower()
    
    # Only ROAS, CTR, and Conversion Rate should have decimal places
    # Check for various spellings and abbreviations that might appear in original column names
    if any(term in metric_lower for term in ['roas', 'return on ad spend', 'return on adspend', 'roi']):
        return round(value, 1)  # 1 decimal place for ROAS
    elif any(term in metric_lower for term in ['ctr', 'click through', 'click-through', 'click rate']):
        return round(value, 2)  # 2 decimal places for CTR
    elif any(term in metric_lower for term in ['conv rate', 'conversion rate', 'cvr', 'conv. rate']):
        return round(value, 2)  # 2 decimal places for Conversion Rate
    else:
        # All other metrics are integers
        return round(value)

def generate_default_metrics():
    """
    Generate a set of default metrics if no metrics can be extracted.
    
    Returns:
        list: List of default metric dictionaries
    """
    return [
        {
            'name': 'Clicks',
            'current': round(np.random.uniform(800, 12000)),
            'simulated': 0,
            'impact': 0.0
        },
        {
            'name': 'Conversions',
            'current': round(np.random.uniform(50, 800)),
            'simulated': 0,
            'impact': 0.0
        },
        {
            'name': 'ROAS',
            'current': round(np.random.uniform(1.8, 4.2), 1),
            'simulated': 0,
            'impact': 0.0
        }
    ]

def determine_platform(df, filename, file_format):
    """
    Determine the ad platform based on file content and name.
    
    Args:
        df: DataFrame containing the data
        filename: Original filename
        file_format: Detected file format
        
    Returns:
        str: Platform name
    """
    # Check file format detection
    if file_format['source'] == 'google_ads':
        return 'Google'
    elif file_format['source'] == 'meta':
        return 'Meta'
    
    # Check column names
    columns = df.columns.str.lower()
    if any(col.find('google') >= 0 for col in columns):
        return 'Google'
    elif any(col.find('meta') >= 0 for col in columns) or any(col.find('facebook') >= 0 for col in columns):
        return 'Meta'
    elif any(col.find('amazon') >= 0 for col in columns):
        return 'Amazon'
    
    # Check filename
    filename_lower = filename.lower()
    if 'google' in filename_lower or 'ads' in filename_lower:
        return 'Google'
    elif 'meta' in filename_lower or 'facebook' in filename_lower or 'fb' in filename_lower:
        return 'Meta'
    elif 'amazon' in filename_lower:
        return 'Amazon'
    
    # Default
    return 'Unknown'

def extract_campaign_name(df, filename):
    """
    Extract campaign name from file data or filename.
    
    Args:
        df: DataFrame containing the data
        filename: Original filename
        
    Returns:
        str: Campaign name
    """
    # Try to find campaign name in the data
    if 'Campaign' in df.columns:
        # Get the most frequent campaign name
        campaigns = df['Campaign'].value_counts()
        if not campaigns.empty:
            return campaigns.index[0]
    
    # If there's a campaign column with a different name
    campaign_cols = [col for col in df.columns if 'campaign' in col.lower()]
    if campaign_cols:
        campaigns = df[campaign_cols[0]].value_counts()
        if not campaigns.empty:
            return campaigns.index[0]
    
    # Extract from filename (remove extension and common prefixes)
    name = filename.rsplit('.', 1)[0]
    for prefix in ['report_', 'export_', 'data_', 'campaign_']:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
    
    # If name is still too generic, use "All Campaigns"
    if name.lower() in ['report', 'export', 'data', 'campaigns']:
        return 'All Campaigns'
    
    return name
