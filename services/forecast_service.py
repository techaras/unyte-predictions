from prophet import Prophet
import pandas as pd
from config import logger
from services.viz_service import create_forecast_plots

def generate_forecast(df, date_col, metrics, forecast_period):
    """
    Generate forecasts using Prophet for selected metrics with the specified date column.
    
    Args:
        df: DataFrame containing the data
        date_col: Name of the date column
        metrics: List of metrics to forecast
        forecast_period: Number of periods to forecast
        
    Returns:
        dict: Dictionary of forecast results
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
            
            # Create visualizations and get paths
            plot_path, components_path = create_forecast_plots(prophet_df, forecast, metric)
            
            # Store results
            results[metric] = {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_period).to_dict('records'),
                'plot_path': plot_path,
                'components_path': components_path
            }
        except Exception as e:
            logger.error(f"Error forecasting {metric}: {e}")
            continue
    
    return results