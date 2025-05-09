import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from config import logger, UPLOAD_FOLDER
from utils.file_utils import allowed_file, generate_unique_filename
from services.file_service import process_uploaded_file, prepare_data_for_forecast, calculate_budget_data
from services.forecast_service import generate_forecast
from utils.date_utils import convert_column_to_datetime
from datetime import datetime
from utils.export_utils import save_forecast_data, load_forecast_data, generate_forecast_csv_from_file

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.index'))
    
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('main.index'))
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        try:
            # Process the uploaded file
            df, date_cols, numeric_cols, detected_date_format, file_format = process_uploaded_file(file_path)
            
            # Calculate budget data
            budget_data = calculate_budget_data(df, file_format)
            logger.info(f"Calculated budget data: daily avg = {budget_data['dailyAverage']} {budget_data['currency']}")
            
            if not date_cols:
                error_msg = 'No date column found. Please ensure your CSV has a column with dates.'
                logger.error(error_msg)
                flash(error_msg)
                os.remove(file_path)
                return redirect(url_for('main.index'))
                
            if not numeric_cols:
                error_msg = 'No numeric columns found to forecast.'
                logger.error(error_msg)
                flash(error_msg)
                os.remove(file_path)
                return redirect(url_for('main.index'))
            
            # Get the selected date column (first/only one in the list)
            selected_date_col = date_cols[0]
            
            # Get the last date from the CSV
            try:
                # Make sure the date column is in datetime format
                df = convert_column_to_datetime(df, selected_date_col, detected_date_format)
                
                # Sort by date and get the last date
                df = df.sort_values(by=selected_date_col)
                last_date = df[selected_date_col].iloc[-1]
                
                # Format the last date as ISO format string for the template
                last_date_str = last_date.strftime('%Y-%m-%d')
                logger.info(f"Last date in CSV: {last_date_str}")
            except Exception as e:
                logger.warning(f"Could not determine last date from CSV: {e}")
                # Use today as fallback
                last_date_str = datetime.today().strftime('%Y-%m-%d')
                logger.info(f"Using today as fallback for last date: {last_date_str}")
            
            # Store the filename and format info in session to retrieve it later
            session['uploaded_file'] = unique_filename
            session['original_filename'] = file.filename
            session['file_format'] = file_format
            session['detected_date_format'] = detected_date_format
            session['selected_date_col'] = selected_date_col
            session['last_date'] = last_date_str  # Store the last date in session
            session['budget_data'] = budget_data  # Store budget data in session
            
            logger.info(f"Automatically selected date column: {selected_date_col}")
            
            # Pass the selected date column and last date to the template
            return render_template('select_columns.html', 
                                  date_cols=date_cols,
                                  selected_date_col=selected_date_col,
                                  numeric_cols=numeric_cols,
                                  detected_format=detected_date_format,
                                  original_filename=file.filename,
                                  last_date=last_date_str,  # Pass last date to template
                                  budget_data=budget_data,
                                  file_format=file_format)  # Pass budget data to template
                
        except Exception as e:
            error_message = f'Error processing file: {str(e)}'
            logger.error(error_message)
            flash(error_message)
            # Clean up the file
            if os.path.exists(file_path):
                os.remove(file_path)
            return redirect(url_for('main.index'))
    else:
        flash('File type not allowed. Please upload a CSV file.')
        return redirect(url_for('main.index'))

@main.route('/process', methods=['POST'])
def process():
    # Get the forecast period and selected metrics
    selected_metrics = request.form.getlist('metrics')
    forecast_period = int(request.form.get('forecast_period', 30))
    date_format = request.form.get('date_format', session.get('detected_date_format', 'auto'))
    
    # Get forecast title
    forecast_title = request.form.get('forecast_title', 'Forecast')
    
    # Get estimated budget and calculate budget change ratio
    try:
        # Get new budget from form
        estimated_budget = float(request.form.get('estimated_budget', 0))
        
        # Get original budget data from session
        budget_data = session.get('budget_data', {})
        daily_average = budget_data.get('dailyAverage', 0)
        
        # Calculate total original budget for the forecast period
        original_total_budget = daily_average * forecast_period
        
        # Calculate budget change ratio (default to 1.0 if original budget is too small)
        if original_total_budget > 1.0:  # Avoid division by very small numbers
            budget_change_ratio = estimated_budget / original_total_budget
        else:
            budget_change_ratio = 1.0
            
        logger.info(f"Original daily budget: {daily_average}, Total original budget: {original_total_budget}")
        logger.info(f"New total budget: {estimated_budget}, Budget change ratio: {budget_change_ratio}")
    except ValueError:
        estimated_budget = 0
        budget_change_ratio = 1.0
    
    # Get currency from budget_data in session
    budget_data = session.get('budget_data', {})
    currency = '£'  # Force currency to be '£'
    
    # Get campaign end date if provided
    campaign_end_date = request.form.get('campaign_end_date')
    if campaign_end_date:
        logger.info(f"Campaign end date received: {campaign_end_date}")
    
    # Calculate date range
    last_date_str = session.get('last_date')
    start_date = datetime.strptime(last_date_str, '%Y-%m-%d') if last_date_str else datetime.today()
    end_date = datetime.strptime(campaign_end_date, '%Y-%m-%d') if campaign_end_date else start_date
    date_range = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    
    # Get platform info
    file_format = session.get('file_format', {})
    platform_source = file_format.get('source', 'unknown')
    
    # Map source to display name
    platform_display = {
        'google_ads': 'Google Ads',
        'meta': 'Meta Ads', 
        'amazon': 'Amazon Ads',
        'unknown': 'Unknown Platform'
    }.get(platform_source, 'Unknown Platform')
    
    # Use the date column that was automatically selected
    date_col = session.get('selected_date_col')
    if not date_col:
        flash('No date column selected. Please try again.')
        return redirect(url_for('main.index'))
    
    # Get the uploaded file path from session
    if 'uploaded_file' not in session:
        flash('No file found. Please upload again.')
        return redirect(url_for('main.index'))
    
    file_path = os.path.join(UPLOAD_FOLDER, session['uploaded_file'])
    
    if not os.path.exists(file_path):
        flash('File not found. Please upload again.')
        return redirect(url_for('main.index'))
    
    try:
        # Get file format from session or re-detect it
        file_format = session.get('file_format')
        
        # Prepare data for forecasting
        df = prepare_data_for_forecast(file_path, file_format, date_col, date_format, selected_metrics)
        
        # Generate forecasts with budget change ratio
        results = generate_forecast(
            df, 
            date_col, 
            selected_metrics, 
            forecast_period, 
            budget_change_ratio=budget_change_ratio
        )
        
        # Clean up the file
        os.remove(file_path)
        
        # Save forecast data to temp file and get ID instead of storing in session
        forecast_id = save_forecast_data(
            results, 
            forecast_title, 
            platform_display, 
            estimated_budget, 
            currency, 
            date_range,
            budget_change_ratio=budget_change_ratio  # Add budget change info to saved data
        )
        
        # Only store the forecast ID in session
        session['forecast_id'] = forecast_id
        
        # Clean up upload-related session variables
        session.pop('uploaded_file', None)
        session.pop('original_filename', None)
        session.pop('detected_date_format', None)
        session.pop('file_format', None)
        session.pop('selected_date_col', None)
        session.pop('last_date', None)
        session.pop('budget_data', None)
        
        # Pass all forecast metadata to the template
        return render_template('results.html', 
                              results=results,
                              forecast_title=forecast_title,
                              platform=platform_display,
                              budget=estimated_budget,
                              currency=currency,
                              date_range=date_range,
                              budget_change_ratio=budget_change_ratio,  # Pass budget change to template
                              forecast_id=forecast_id)
    
    except Exception as e:
        error_message = f'Error processing file: {str(e)}'
        logger.error(error_message)
        flash(error_message)
        # Clean up the file
        if os.path.exists(file_path):
            os.remove(file_path)
        # Clean up all session data on error
        session.pop('uploaded_file', None)
        session.pop('original_filename', None)
        session.pop('detected_date_format', None)
        session.pop('file_format', None)
        session.pop('selected_date_col', None)
        session.pop('last_date', None)
        session.pop('budget_data', None)
        session.pop('forecast_id', None)
        return redirect(url_for('main.index'))
    
@main.route('/download_forecast/<forecast_id>')
def download_forecast(forecast_id):
    """Generate and download forecast results as CSV using stored forecast ID."""
    # Load forecast data from temp file
    forecast_data = load_forecast_data(forecast_id)
    
    if not forecast_data:
        flash('No forecast data available for download. Please generate a forecast first.')
        return redirect(url_for('main.index'))
    
    # Generate CSV file
    csv_data = generate_forecast_csv_from_file(forecast_id)
    
    if not csv_data:
        flash('Error generating CSV file.')
        return redirect(url_for('main.index'))
    
    # Create a safe filename
    forecast_title = forecast_data['metadata']['forecast_title']
    safe_filename = forecast_title.replace(' ', '_').replace('/', '-')
    
    # Return the CSV file as a download
    return send_file(
        csv_data,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{safe_filename}_forecast.csv"
    )