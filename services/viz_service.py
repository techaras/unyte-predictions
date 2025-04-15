import plotly.graph_objects as go
import plotly.offline as pyo
import pandas as pd
from datetime import datetime
from config import logger

def create_forecast_plots(prophet_df, forecast, metric, budget_change_ratio=1.0):
    """
    Create forecast and component plots using Plotly.
    
    Args:
        prophet_df: DataFrame with historical data
        forecast: DataFrame with forecast data from Prophet
        metric: Name of the metric being forecasted
        budget_change_ratio: The ratio of budget change applied to the forecast
        
    Returns:
        tuple: (forecast_plot_path, components_plot_path)
    """
    # Create Plotly visualization
    # Forecast plot
    plot_id = f"{metric}_plot_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Determine the forecast period by finding future dates
    last_historical_date = prophet_df['ds'].max()
    future_dates = forecast[forecast['ds'] > last_historical_date]
    forecast_period = len(future_dates)
    
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
    
    # Add confidence intervals (uncertainty)
    fig_forecast.add_trace(go.Scatter(
        x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
        y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(0,176,246,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="95% Confidence Interval"
    ))
    
    # Add a vertical line where forecast begins
    fig_forecast.add_shape(
        type="line",
        x0=last_historical_date,
        y0=0,
        x1=last_historical_date,
        y1=forecast['yhat'].max() * 1.1,
        line=dict(color="gray", width=1, dash="dash"),
    )
    
    # Add annotation about budget change if different from 1.0
    if abs(budget_change_ratio - 1.0) > 0.01:  # If budget changed by more than 1%
        budget_change_text = f"Budget impact: {budget_change_ratio:.2f}x"
        
        # Extract budget effect magnitude if available
        if 'budget_normalized_effect' in forecast.columns:
            effect = forecast.loc[forecast['ds'] > last_historical_date, 'budget_normalized_effect']
            if not effect.empty:
                avg_effect = effect.mean()
                metric_avg = prophet_df['y'].mean()
                
                # Only add percent effect if metric mean is not too close to zero
                if abs(metric_avg) > 0.001:
                    pct_effect = avg_effect / metric_avg * 100
                    budget_change_text += f" (~{pct_effect:.1f}% impact)"
        
        # Calculate a position about 20% into the forecast period
        annotation_date = last_historical_date + pd.Timedelta(days=max(1, int(forecast_period * 0.2)))
        
        # Add annotation
        fig_forecast.add_annotation(
            x=annotation_date,
            y=forecast['yhat'].max() * 0.9,
            text=budget_change_text,
            showarrow=True,
            arrowhead=1,
            arrowcolor="black",
            font=dict(color="black", size=12),
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
        )
    
    fig_forecast.update_layout(
        title=f'{metric} Forecast' + (f' (Budget: {budget_change_ratio:.2f}x)' if abs(budget_change_ratio - 1.0) > 0.01 else ''),
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
    
    components_path = None
    
    if valid_components:
        fig_comp = go.Figure()
        
        for component in valid_components:
            fig_comp.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast[component],
                mode='lines',
                name=component
            ))
        
        # Add budget impact to components plot
        if 'budget_normalized_effect' in forecast.columns:
            fig_comp.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['budget_normalized_effect'],
                mode='lines',
                name='Budget Effect',
                line=dict(color='green', width=2)
            ))
            
            # Add a zero line for reference
            fig_comp.add_shape(
                type="line",
                x0=forecast['ds'].min(),
                y0=0,
                x1=forecast['ds'].max(),
                y1=0,
                line=dict(color="lightgray", width=1, dash="dot"),
            )
        
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
    
    return plot_path.replace('static/', ''), components_path.replace('static/', '') if components_path else None