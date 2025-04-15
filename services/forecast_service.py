from prophet import Prophet
import pandas as pd
import numpy as np
from config import logger
from services.viz_service import create_forecast_plots

def generate_forecast(df, date_col, metrics, forecast_period, budget_change_ratio=1.0):
    """
    Generate forecasts using Prophet for selected metrics with the specified date column.
    Incorporates budget changes as a regressor with metric-specific elasticities.
    
    Args:
        df: DataFrame containing the data
        date_col: Name of the date column
        metrics: List of metrics to forecast
        forecast_period: Number of periods to forecast
        budget_change_ratio: Ratio of new budget to original budget (default: 1.0 = no change)
        
    Returns:
        dict: Dictionary of forecast results including elasticity data
    """
    results = {}
    elasticity_data = {}
    
    # Add budget regressor to the dataframe (historical values are normalized to 1.0)
    df['budget_normalized'] = 1.0
    
    # Ensure the date column is properly formatted
    df = df.dropna(subset=[date_col])
    
    # Calculate an elasticity index for adjusting budget effects later
    min_observations = 5  # Minimum data points needed to calculate reliable elasticity
    
    for metric in metrics:
        # Skip if it's the date column
        if metric == date_col:
            continue
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = df[[date_col, metric, 'budget_normalized']].rename(columns={date_col: 'ds', metric: 'y'})
        prophet_df = prophet_df.dropna()
        
        if prophet_df.empty or len(prophet_df) < min_observations:
            logger.warning(f"Not enough valid data for metric: {metric}")
            continue
        
        logger.info(f"Forecasting for metric: {metric} with {len(prophet_df)} data points")
        logger.info(f"Using budget change ratio: {budget_change_ratio}")
        
        try:
            # Create and fit model
            model = Prophet()
            
            # Add budget as a regressor
            model.add_regressor('budget_normalized')
            
            model.fit(prophet_df)
            
            # Extract budget elasticity - use a simpler, more robust approach
            try:
                # Method 1: Direct calculation of elasticity through counterfactual forecasting
                # Create two future dataframes with different budget values
                base_future = model.make_future_dataframe(periods=1)
                base_future['budget_normalized'] = 1.0  # Base budget
                
                increased_future = model.make_future_dataframe(periods=1)
                increased_future['budget_normalized'] = 1.1  # 10% increase
                
                # Make predictions for both scenarios
                base_pred = model.predict(base_future)
                increased_pred = model.predict(increased_future)
                
                # Calculate elasticity as % change in forecast / % change in budget
                last_base = base_pred['yhat'].iloc[-1]
                last_increased = increased_pred['yhat'].iloc[-1]
                
                # Avoid division by zero
                if abs(last_base) > 0.001:
                    pct_change_in_metric = (last_increased - last_base) / last_base
                    pct_change_in_budget = 0.1  # 10% increase
                    budget_elasticity = pct_change_in_metric / pct_change_in_budget
                else:
                    budget_elasticity = 1.0  # Default if base value is too close to zero
                
                logger.info(f"Calculated budget elasticity for {metric}: {budget_elasticity}")
                
                # Store the elasticity value
                elasticity_data[metric] = {
                    'coefficient': float(budget_elasticity),
                    'data_points': len(prophet_df)
                }
            except Exception as e:
                # If we can't extract the coefficient, set a default value
                logger.warning(f"Could not calculate budget elasticity for {metric}: {e}")
                budget_elasticity = 1.0  # Default to 1:1 relationship
                elasticity_data[metric] = {
                    'coefficient': float(budget_elasticity),
                    'data_points': len(prophet_df)
                }
            
            # Create future dataframe for the actual forecast
            future = model.make_future_dataframe(periods=forecast_period)
            
            # Set future budget values based on budget_change_ratio
            future['budget_normalized'] = 1.0  # Default for historical dates
            
            # Apply budget change only to the forecast period
            future.loc[future['ds'] > prophet_df['ds'].max(), 'budget_normalized'] = budget_change_ratio
            
            # Make prediction
            forecast = model.predict(future)
            
            # Calculate the budget effect component 
            try:
                # Simple direct calculation of budget effect
                base_future = future.copy()
                base_future['budget_normalized'] = 1.0  # Default budget everywhere
                
                # Predict with default budget
                base_forecast = model.predict(base_future)
                
                # Budget effect is the difference between forecasts with and without budget change
                budget_effect = forecast['yhat'] - base_forecast['yhat']
                
                # Only apply to future dates
                budget_effect.loc[future['ds'] <= prophet_df['ds'].max()] = 0
                
                # Add to forecast components
                forecast['budget_normalized_effect'] = budget_effect
            except Exception as e:
                logger.warning(f"Could not calculate budget effect component: {e}")
                # Create a dummy effect column
                forecast['budget_normalized_effect'] = 0.0
            
            # Create visualizations and get paths
            plot_path, components_path = create_forecast_plots(prophet_df, forecast, metric, budget_change_ratio)
            
            # Add additional elasticity context to results
            results[metric] = {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_period).to_dict('records'),
                'plot_path': plot_path,
                'components_path': components_path,
                'elasticity': {
                    'coefficient': float(budget_elasticity),
                    'normalized_impact': float(budget_elasticity * budget_change_ratio / prophet_df['y'].mean()) 
                        if prophet_df['y'].mean() > 0 else 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error forecasting {metric}: {e}")
            continue
    
    # Add relative elasticity scores for comparisons across metrics
    if elasticity_data:
        # Get min and max elasticities for normalization
        elasticity_values = [data['coefficient'] for data in elasticity_data.values()]
        min_elasticity = min(elasticity_values)
        max_elasticity = max(elasticity_values)
        elasticity_range = max_elasticity - min_elasticity
        
        # Normalize elasticities to a 0-10 scale for easy comparison
        for metric, data in elasticity_data.items():
            if elasticity_range > 0:
                normalized_elasticity = ((data['coefficient'] - min_elasticity) / elasticity_range) * 10
            else:
                normalized_elasticity = 5.0  # Default middle value if all metrics have same elasticity
                
            if metric in results:
                results[metric]['elasticity']['normalized_score'] = float(normalized_elasticity)
                
                # Add interpretation of elasticity
                if normalized_elasticity < 3.33:
                    results[metric]['elasticity']['response'] = "Low budget sensitivity"
                elif normalized_elasticity < 6.67:
                    results[metric]['elasticity']['response'] = "Medium budget sensitivity"
                else:
                    results[metric]['elasticity']['response'] = "High budget sensitivity"
    
    return results