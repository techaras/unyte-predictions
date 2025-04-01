import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config import logger, UPLOAD_FOLDER
from utils.file_utils import allowed_file, generate_unique_filename
from services.file_service import process_uploaded_file, prepare_data_for_forecast
from services.forecast_service import generate_forecast

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
            
            # Store the filename and format info in session to retrieve it later
            session['uploaded_file'] = unique_filename
            session['file_format'] = file_format
            session['detected_date_format'] = detected_date_format
            # Store the selected date column (first/only one in the list)
            session['selected_date_col'] = date_cols[0]
            
            logger.info(f"Automatically selected date column: {date_cols[0]}")
            
            # Pass the selected date column to the template
            return render_template('select_columns.html', 
                                  date_cols=date_cols,  # Still pass this for backward compatibility
                                  selected_date_col=date_cols[0],  # But explicitly pass the selected one
                                  numeric_cols=numeric_cols,
                                  detected_format=detected_date_format)
                
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
        
        # Generate forecasts
        results = generate_forecast(df, date_col, selected_metrics, forecast_period)
        
        # Clean up the file
        os.remove(file_path)
        session.pop('uploaded_file', None)
        session.pop('detected_date_format', None)
        session.pop('file_format', None)
        session.pop('selected_date_col', None)
        
        return render_template('results.html', results=results)
    
    except Exception as e:
        error_message = f'Error processing file: {str(e)}'
        logger.error(error_message)
        flash(error_message)
        # Clean up the file
        if os.path.exists(file_path):
            os.remove(file_path)
        session.pop('uploaded_file', None)
        session.pop('detected_date_format', None)
        session.pop('file_format', None)
        session.pop('selected_date_col', None)
        return redirect(url_for('main.index'))