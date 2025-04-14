import plotly.graph_objects as go
import plotly.offline as pyo
from datetime import datetime
from config import logger

def create_forecast_plots(prophet_df, forecast, metric):
    """
    Create forecast and component plots using Plotly.
    
    Args:
        prophet_df: DataFrame with historical data
        forecast: DataFrame with forecast data from Prophet
        metric: Name of the metric being forecasted
        
    Returns:
        tuple: (forecast_plot_path, components_plot_path)
    """
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
    # fig_forecast.add_trace(go.Scatter(
    #     x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
    #     y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
    #     fill='toself',
    #     fillcolor='rgba(0,176,246,0.2)',
    #     line=dict(color='rgba(255,255,255,0)'),
    #     hoverinfo="skip",
    #     showlegend=False
    # ))
    
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