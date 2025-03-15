import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import plotly.offline as pyo
from datetime import datetime
import uuid
import logging

app = Flask(__name__)
app.secret_key = "unyte_predictions_secret_key"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create upload and plots folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/plots', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def parse_dates_with_format_detection(df, date_col):
    """Try to detect date format and parse dates accordingly.
    
    Args:
        df: DataFrame containing date column
        date_col: Name of the column containing dates
        
    Returns:
        tuple: (parsed_dates, detected_format)
    """
    # First try automatic parsing
    dates_auto = pd.to_datetime(df[date_col], errors='coerce')
    
    # Try explicit formats
    dates_mdy = pd.to_datetime(df[date_col], format='%m/%d/%Y', errors='coerce')
    dates_dmy = pd.to_datetime(df[date_col], format='%d/%m/%Y', errors='coerce')
    
    # Count valid dates for each method
    valid_auto = (~dates_auto.isna()).sum()
    valid_mdy = (~dates_mdy.isna()).sum()
    valid_dmy = (~dates_dmy.isna()).sum()
    
    # Choose the format that successfully parsed the most dates
    if valid_mdy >= valid_auto and valid_mdy >= valid_dmy:
        logger.info(f"Detected American date format (MM/DD/YYYY) for column {date_col}")
        return dates_mdy, '%m/%d/%Y'
    elif valid_dmy >= valid_auto:
        logger.info(f"Detected European date format (DD/MM/YYYY) for column {date_col}")
        return dates_dmy, '%d/%m/%Y'
    else:
        logger.info(f"Using auto-detected date format for column {date_col}")
        return dates_auto, 'auto'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        unique_filename = str(uuid.uuid4()) + '.csv'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        try:
            # For Google Ads CSV files, we need to skip the first 2 rows
            # because they contain metadata, not actual headers
            df = pd.read_csv(file_path, skiprows=2)
            logger.info(f"Successfully read CSV with skiprows=2. Columns: {df.columns.tolist()}")
            
            # Make sure 'Day' is properly formatted as a date column
            detected_date_format = 'auto'
            if 'Day' in df.columns:
                df['Day'], detected_date_format = parse_dates_with_format_detection(df, 'Day')
                if not df['Day'].isna().all():
                    date_cols = ['Day']
                    logger.info(f"Successfully formatted 'Day' as a date column using format: {detected_date_format}")
                else:
                    logger.warning("Failed to convert 'Day' to date format")
                    date_cols = []
            else:
                # Look for other potential date columns
                date_cols = []
                logger.warning("'Day' column not found in CSV, looking for other date columns")
                
                # Check if there are any columns containing 'date' or 'day' in the name
                date_candidates = [col for col in df.columns if 'date' in col.lower() or 'day' in col.lower()]
                
                if date_candidates:
                    for col in date_candidates:
                        parsed_dates, format_detected = parse_dates_with_format_detection(df, col)
                        if not parsed_dates.isna().all():
                            df[col] = parsed_dates
                            date_cols.append(col)
                            detected_date_format = format_detected
                            logger.info(f"Found date column: {col} with format {format_detected}")
                            break
                
                if not date_cols:
                    # If no obvious date columns found, try all string columns
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            # Check if column might contain dates (simple check for / or -)
                            sample_val = str(df[col].iloc[0]) if not df[col].empty else ""
                            if '/' in sample_val or '-' in sample_val:
                                parsed_dates, format_detected = parse_dates_with_format_detection(df, col)
                                if not parsed_dates.isna().all():
                                    df[col] = parsed_dates
                                    date_cols.append(col)
                                    detected_date_format = format_detected
                                    logger.info(f"Found date column: {col} with format {format_detected}")
                                    break
            
            # Store detected format in session
            session['detected_date_format'] = detected_date_format
            
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
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            logger.info(f"Numeric columns: {numeric_cols}")
            
            if not date_cols:
                error_msg = 'No date column found. Please ensure your CSV has a column with dates.'
                logger.error(error_msg)
                flash(error_msg)
                os.remove(file_path)
                return redirect(url_for('index'))
                
            if not numeric_cols:
                error_msg = 'No numeric columns found to forecast.'
                logger.error(error_msg)
                flash(error_msg)
                os.remove(file_path)
                return redirect(url_for('index'))
            
            # Store the filename in session to retrieve it later
            session['uploaded_file'] = unique_filename
            return render_template('select_columns.html', 
                                   date_cols=date_cols, 
                                   numeric_cols=numeric_cols,
                                   detected_format=detected_date_format)
                
        except Exception as e:
            error_message = f'Error processing file: {str(e)}'
            logger.error(error_message)
            flash(error_message)
            # Clean up the file
            if os.path.exists(file_path):
                os.remove(file_path)
            return redirect(url_for('index'))
    else:
        flash('File type not allowed. Please upload a CSV file.')
        return redirect(url_for('index'))

@app.route('/process', methods=['POST'])
def process():
    # Get the selected columns and forecast period
    date_col = request.form.get('date_col')
    selected_metrics = request.form.getlist('metrics')
    forecast_period = int(request.form.get('forecast_period', 30))
    date_format = request.form.get('date_format', session.get('detected_date_format', 'auto'))
    
    # Get the uploaded file path from session
    if 'uploaded_file' not in session:
        flash('No file found. Please upload again.')
        return redirect(url_for('index'))
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], session['uploaded_file'])
    
    if not os.path.exists(file_path):
        flash('File not found. Please upload again.')
        return redirect(url_for('index'))
    
    try:
        # Read the CSV file with specific handling for Google Ads format
        df = pd.read_csv(file_path, skiprows=2)
        
        # Convert date column to datetime using the selected format
        if date_format == 'auto':
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            logger.info(f"Using automatic date parsing for column {date_col}")
        else:
            df[date_col] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
            logger.info(f"Using format {date_format} for column {date_col}")
        
        # Clean numeric data - remove commas from numbers
        for col in selected_metrics:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Generate forecasts
        results = generate_forecast(df, date_col, selected_metrics, forecast_period)
        
        # Clean up the file
        os.remove(file_path)
        session.pop('uploaded_file', None)
        session.pop('detected_date_format', None)
        
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
        return redirect(url_for('index'))

def generate_forecast(df, date_col, metrics, forecast_period):
    """
    Generate forecasts using Prophet for selected metrics with the specified date column.
    """
    results = {}
    
    # Ensure the date column is properly formatted
    df = df.dropna(subset=[date_col])
    
    for metric in metrics:
        # Skip if it's the date column
        if metric == date_col:
            continue
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = df[[date_col, metric]].rename(columns={date_col: 'ds', metric: 'y'})
        prophet_df = prophet_df.dropna()
        
        if prophet_df.empty:
            logger.warning(f"No valid data for metric: {metric}")
            continue
        
        logger.info(f"Forecasting for metric: {metric} with {len(prophet_df)} data points")
        
        try:
            # Create and fit model
            model = Prophet()
            model.fit(prophet_df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=forecast_period)
            
            # Make prediction
            forecast = model.predict(future)
            
            # Create Plotly visualization
            # Forecast plot
            plot_id = f"{metric}_plot_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Historical data
            fig_forecast = go.Figure()
            fig_forecast.add_trace(go.Scatter(
                x=prophet_df['ds'],
                y=prophet_df['y'],
                mode='markers',
                name='Historical',
                marker=dict(color='blue', size=4)
            ))
            
            # Forecast
            fig_forecast.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat'],
                mode='lines',
                name='Forecast',
                line=dict(color='red')
            ))
            
            # Uncertainty interval
            fig_forecast.add_trace(go.Scatter(
                x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
                y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0,176,246,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=False
            ))
            
            fig_forecast.update_layout(
                title=f'{metric} Forecast',
                xaxis_title='Date',
                yaxis_title=metric,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Save as HTML
            plot_path = f'static/plots/{plot_id}.html'
            pyo.plot(fig_forecast, filename=plot_path, auto_open=False)
            
            # Components plot (trends, weekly patterns, etc.)
            components = ['trend', 'weekly', 'yearly']
            valid_components = [c for c in components if c in forecast.columns]
            
            if valid_components:
                fig_comp = go.Figure()
                
                for component in valid_components:
                    fig_comp.add_trace(go.Scatter(
                        x=forecast['ds'],
                        y=forecast[component],
                        mode='lines',
                        name=component
                    ))
                
                fig_comp.update_layout(
                    title=f'{metric} Components',
                    xaxis_title='Date',
                    yaxis_title='Value',
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                components_id = f"{metric}_components_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                components_path = f'static/plots/{components_id}.html'
                pyo.plot(fig_comp, filename=components_path, auto_open=False)
            else:
                components_path = None
            
            # Store results
            results[metric] = {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_period).to_dict('records'),
                'plot_path': plot_path.replace('static/', ''),
                'components_path': components_path.replace('static/', '') if components_path else None
            }
        except Exception as e:
            logger.error(f"Error forecasting {metric}: {e}")
            continue
    
    return results

if __name__ == '__main__':
    app.run(debug=True)