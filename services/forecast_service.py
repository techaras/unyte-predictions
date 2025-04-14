from prophet import Prophet
import pandas as pd
from config import logger
from services.viz_service import create_forecast_plots

def generate_forecast(df, date_col, metrics, forecast_period, budget_col=None, projected_budget=None):
    """
    Generate forecasts using Prophet for selected metrics with the specified date column.
    
    Args:
        df: DataFrame containing the data
        date_col: Name of the date column
        metrics: List of metrics to forecast
        forecast_period: Number of periods to forecast
        budget_col: Column containing budget/spend data
        projected_budget: Future daily budget to use for forecast
        
    Returns:
        dict: Dictionary of forecast results with elasticity data
    """
    results = {}
    
    # Ensure the date column is properly formatted
    df = df.dropna(subset=[date_col])
    
    # Calculate average daily budget from historical data if we have a budget column
    historical_daily_budget = None
    if budget_col and budget_col in df.columns:
        try:
            # Group by date to avoid double-counting
            daily_budget_df = df.groupby(date_col)[budget_col].sum().reset_index()
            historical_daily_budget = daily_budget_df[budget_col].mean()
            logger.info(f"Historical daily budget: {historical_daily_budget}")
            
            # Filter out zero budget values
            if len(daily_budget_df[daily_budget_df[budget_col] > 0]) > 0:
                filtered_daily_budget_df = daily_budget_df[daily_budget_df[budget_col] > 0]
                historical_daily_budget = filtered_daily_budget_df[budget_col].mean()
                logger.info(f"Historical daily budget (non-zero values only): {historical_daily_budget}")
        except Exception as e:
            logger.warning(f"Could not calculate historical daily budget: {e}")
    
    for metric in metrics:
        # Skip if it's the date column or budget column
        if metric == date_col or metric == budget_col:
            continue
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        if budget_col and budget_col in df.columns:
            # Include budget column for regression
            prophet_df = df[[date_col, metric, budget_col]].rename(
                columns={date_col: 'ds', metric: 'y', budget_col: 'budget'}
            )
        else:
            prophet_df = df[[date_col, metric]].rename(columns={date_col: 'ds', metric: 'y'})
        
        prophet_df = prophet_df.dropna()
        
        # Filter out zero budget values if budget column exists
        if 'budget' in prophet_df.columns:
            zero_budget_count = (prophet_df['budget'] == 0).sum()
            if zero_budget_count > 0:
                logger.info(f"Filtering out {zero_budget_count} rows with zero budget")
                prophet_df = prophet_df[prophet_df['budget'] > 0]
        
        if prophet_df.empty:
            logger.warning(f"No valid data for metric: {metric}")
            continue
        
        logger.info(f"Forecasting for metric: {metric} with {len(prophet_df)} data points")
        
        try:
            # Add synthetic budget variation if needed
            if 'budget' in prophet_df.columns:
                budget_variation = prophet_df['budget'].nunique()
                budget_min = prophet_df['budget'].min()
                budget_max = prophet_df['budget'].max()
                budget_mean = prophet_df['budget'].mean()
                
                logger.info(f"Budget column values: unique={budget_variation}, min={budget_min}, max={budget_max}, mean={budget_mean}")
                
                # If limited budget variation (less than 3 unique values), add synthetic data
                if budget_variation < 3:
                    logger.info(f"Limited budget variation detected ({budget_variation} unique values). Adding synthetic data.")
                    
                    # Create a copy of data with slightly varied budgets
                    synthetic_low = prophet_df.copy()
                    synthetic_low['budget'] = synthetic_low['budget'] * 0.8
                    synthetic_low['y'] = synthetic_low['y'] * 0.9  # Assume 10% less results
                    
                    synthetic_high = prophet_df.copy()
                    synthetic_high['budget'] = synthetic_high['budget'] * 1.2
                    synthetic_high['y'] = synthetic_high['y'] * 1.1  # Assume 10% more results
                    
                    # Combine the data
                    prophet_df = pd.concat([prophet_df, synthetic_low, synthetic_high])
                    logger.info(f"Added synthetic data. New dataset size: {len(prophet_df)} rows")
            
            # Create model
            model = Prophet()
            
            # Add budget as a regressor if available
            budget_elasticity = None
            if budget_col and 'budget' in prophet_df.columns:
                logger.info(f"Adding budget as regressor for {metric}")
                # Use higher prior_scale to emphasize budget relationship
                model.add_regressor('budget', prior_scale=10.0)  # Default is 5.0
            
            # Fit model
            model.fit(prophet_df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=forecast_period)
            
            # Add future budget values if we have budget data
            if budget_col and 'budget' in prophet_df.columns:
                # Set default future budget (use historical average if projected budget not provided)
                future_budget_value = projected_budget if projected_budget is not None else historical_daily_budget
                
                if future_budget_value is not None:
                    logger.info(f"Using future budget value: {future_budget_value} for {metric}")
                    
                    # Set future budget values
                    future['budget'] = future_budget_value
                    
                    # Preserve historical values
                    historical_dates = prophet_df['ds'].tolist()
                    for date in historical_dates:
                        historical_budget = prophet_df.loc[prophet_df['ds'] == date, 'budget'].values
                        if len(historical_budget) > 0:
                            future.loc[future['ds'] == date, 'budget'] = historical_budget[0]
                    
                    # Calculate elasticity if possible
                    try:
                        from prophet.utilities import regressor_coefficients
                        coefs = regressor_coefficients(model)
                        budget_coef = coefs.loc[coefs['regressor'] == 'budget', 'coef'].values[0]
                        
                        # Get baseline average for the metric
                        baseline_avg = prophet_df['y'].mean()
                        
                        # Calculate budget impact
                        budget_impact = budget_coef * future_budget_value
                        
                        # Store elasticity info
                        budget_elasticity = {
                            'coefficient': float(budget_coef),
                            'baseline_avg': float(baseline_avg),
                            'budget_impact': f"{budget_impact:.2f} per unit",
                            'direction': 'positive' if budget_coef > 0 else 'negative' if budget_coef < 0 else 'neutral'
                        }
                        
                        logger.info(f"Budget elasticity for {metric}: coefficient={budget_elasticity['coefficient']}, baseline={budget_elasticity['baseline_avg']}")
                        
                        # Check if coefficient is very small
                        if abs(budget_elasticity['coefficient']) < 0.001:
                            logger.warning(f"Budget coefficient for {metric} is very small, budget changes will have minimal impact on forecast")
                        
                    except Exception as e:
                        logger.warning(f"Could not calculate elasticity for {metric}: {e}")
            
            # Make prediction
            forecast = model.predict(future)
            
            # Create visualizations and get paths
            plot_path, components_path = create_forecast_plots(
                prophet_df, 
                forecast, 
                metric, 
                budget_col='budget' if budget_col and 'budget' in prophet_df.columns else None
            )
            
            # Store results
            results[metric] = {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_period).to_dict('records'),
                'plot_path': plot_path,
                'components_path': components_path
            }
            
            # Add elasticity data if available
            if budget_elasticity:
                results[metric]['elasticity'] = budget_elasticity
                
        except Exception as e:
            logger.error(f"Error forecasting {metric}: {e}")
            continue
    
    return results