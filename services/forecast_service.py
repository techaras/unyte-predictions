from prophet import Prophet
import pandas as pd
from config import logger
from services.viz_service import create_forecast_plots

def generate_forecast(df, date_col, metrics, forecast_period, budget_change_ratio=1.0):
    """
    Generate forecasts using Prophet for selected metrics with the specified date column.
    Incorporates budget changes as a regressor.
    
    Args:
        df: DataFrame containing the data
        date_col: Name of the date column
        metrics: List of metrics to forecast
        forecast_period: Number of periods to forecast
        budget_change_ratio: Ratio of new budget to original budget (default: 1.0 = no change)
        
    Returns:
        dict: Dictionary of forecast results
    """
    results = {}
    
    # Add budget regressor to the dataframe (historical values are normalized to 1.0)
    df['budget_normalized'] = 1.0
    
    # Ensure the date column is properly formatted
    df = df.dropna(subset=[date_col])
    
    for metric in metrics:
        # Skip if it's the date column
        if metric == date_col:
            continue
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = df[[date_col, metric, 'budget_normalized']].rename(columns={date_col: 'ds', metric: 'y'})
        prophet_df = prophet_df.dropna()
        
        if prophet_df.empty:
            logger.warning(f"No valid data for metric: {metric}")
            continue
        
        logger.info(f"Forecasting for metric: {metric} with {len(prophet_df)} data points")
        logger.info(f"Using budget change ratio: {budget_change_ratio}")
        
        try:
            # Create and fit model
            model = Prophet()
            
            # Add budget as a regressor
            model.add_regressor('budget_normalized')
            
            model.fit(prophet_df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=forecast_period)
            
            # Set future budget values based on budget_change_ratio
            future['budget_normalized'] = 1.0  # Default for historical dates
            
            # Apply budget change only to the forecast period
            future.loc[future['ds'] > prophet_df['ds'].max(), 'budget_normalized'] = budget_change_ratio
            
            # Make prediction
            forecast = model.predict(future)
            
            # Create visualizations and get paths
            plot_path, components_path = create_forecast_plots(prophet_df, forecast, metric, budget_change_ratio)
            
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