import csv
import io
import os
import json
import tempfile
from datetime import datetime
import pandas as pd
import uuid

def extract_forecast_data(results):
    """Extract just the necessary forecast data for CSV export."""
    extracted_data = {}
    
    for metric_name, metric_data in results.items():
        forecast_values = []
        for row in metric_data['forecast']:
            forecast_values.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'value': float(row['yhat'])
            })
        extracted_data[metric_name] = forecast_values
    
    return extracted_data

def save_forecast_data(results, forecast_title, platform, budget, currency, date_range):
    """Save forecast data to a temporary file and return the file id."""
    # Extract just the data needed for CSV
    extracted_data = extract_forecast_data(results)
    
    # Create a unique ID for this forecast
    forecast_id = str(uuid.uuid4())
    
    # Prepare metadata
    metadata = {
        'forecast_title': forecast_title,
        'platform': platform,
        'budget': budget,
        'currency': currency,
        'date_range': date_range,
        'generated_on': datetime.now().strftime('%Y-%m-%d'),
        'forecast_id': forecast_id
    }
    
    # Combine data and metadata
    save_data = {
        'metadata': metadata,
        'results': extracted_data
    }
    
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(tempfile.gettempdir(), 'unyte_forecasts')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save to temporary file
    temp_file_path = os.path.join(temp_dir, f"{forecast_id}.json")
    with open(temp_file_path, 'w') as f:
        json.dump(save_data, f)
    
    return forecast_id

def load_forecast_data(forecast_id):
    """Load forecast data from a temporary file."""
    temp_dir = os.path.join(tempfile.gettempdir(), 'unyte_forecasts')
    temp_file_path = os.path.join(temp_dir, f"{forecast_id}.json")
    
    if not os.path.exists(temp_file_path):
        return None
    
    with open(temp_file_path, 'r') as f:
        return json.load(f)

def generate_forecast_csv_from_file(forecast_id):
    """
    Generate a CSV file with forecast results in the specified format.
    
    Args:
        forecast_id: ID of the saved forecast data
        
    Returns:
        BytesIO object containing the CSV data or None if forecast not found
    """
    # Load the forecast data
    forecast_data = load_forecast_data(forecast_id)
    if not forecast_data:
        return None
    
    # Extract metadata
    metadata = forecast_data['metadata']
    results = forecast_data['results']
    
    # Parse date range
    start_date, end_date = [date.strip() for date in metadata['date_range'].split('-')]
    start_date = datetime.strptime(start_date, '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y-%m-%d')
    
    # Calculate forecast period in days
    start_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_obj = datetime.strptime(end_date, '%Y-%m-%d')
    forecast_period = (end_obj - start_obj).days
    
    # Create CSV buffer
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    # Write metadata header
    writer.writerow(['forecast_title', metadata['forecast_title']])
    writer.writerow(['platform', metadata['platform']])
    writer.writerow(['budget', metadata['budget']])
    writer.writerow(['currency', metadata['currency']])
    writer.writerow(['forecast_period', f'{forecast_period} days'])
    writer.writerow(['start_date', start_date])
    writer.writerow(['end_date', end_date])
    writer.writerow(['generated_on', metadata['generated_on']])
    
    # Prepare data rows
    if not results:
        # No results to export
        writer.writerow([])
        return io.BytesIO(csv_buffer.getvalue().encode())
    
    # Get all dates from the first metric
    first_metric = list(results.values())[0]
    dates = [item['date'] for item in first_metric]
    
    # Create a DataFrame to hold all metrics data
    all_data = {}
    
    # Add dates and metric_type columns
    all_data['date'] = dates
    all_data['metric_type'] = ['forecast'] * len(dates)
    
    # Add each metric's forecast values
    for metric_name, metric_data in results.items():
        all_data[metric_name] = [item['value'] for item in metric_data]
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(all_data)
    
    # Get all column names
    column_names = ['date', 'metric_type'] + [m for m in results.keys()]
    
    # Write column headers
    writer.writerow(column_names)
    
    # Write data rows
    for _, row in df.iterrows():
        writer.writerow([row[col] for col in column_names])
    
    # Return as BytesIO object
    csv_buffer.seek(0)
    return io.BytesIO(csv_buffer.getvalue().encode())