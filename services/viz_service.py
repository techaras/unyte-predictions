import plotly.graph_objects as go
import plotly.offline as pyo
from datetime import datetime
from config import logger

def create_forecast_plots(prophet_df, forecast, metric, budget_col=None):
    """
    Create forecast and component plots using Plotly.
    
    Args:
        prophet_df: DataFrame with historical data
        forecast: DataFrame with forecast data from Prophet
        metric: Name of the metric being forecasted
        budget_col: Name of the budget column if available
        
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
    fig_forecast.add_trace(go.Scatter(
        x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
        y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(0,176,246,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False
    ))
    
    # Add budget visualization if available
    if budget_col and budget_col in prophet_df.columns:
        # For historical budget
        fig_forecast.add_trace(go.Scatter(
            x=prophet_df['ds'],
            y=prophet_df[budget_col],
            mode='lines',
            name='Historical Budget',
            yaxis='y2',
            line=dict(color='green', width=1)
        ))
        
        # For future budget (if it differs from historical)
        future_dates = [d for d in forecast['ds'] if d not in prophet_df['ds'].values]
        if future_dates and 'budget' in forecast.columns:
            future_budget = forecast[forecast['ds'].isin(future_dates)]['budget']
            if not future_budget.empty and len(future_budget.unique()) == 1:
                # If constant future budget, show as horizontal line
                fig_forecast.add_trace(go.Scatter(
                    x=future_dates,
                    y=future_budget,
                    mode='lines',
                    name='Projected Budget',
                    yaxis='y2',
                    line=dict(color='darkgreen', width=2, dash='dash')
                ))
            else:
                # If variable future budget
                fig_forecast.add_trace(go.Scatter(
                    x=future_dates,
                    y=future_budget,
                    mode='lines',
                    name='Projected Budget',
                    yaxis='y2',
                    line=dict(color='darkgreen', width=2)
                ))
        
        # Update layout for dual y-axes
        fig_forecast.update_layout(
            yaxis2=dict(
                title='Budget',
                titlefont=dict(color='green'),
                tickfont=dict(color='green'),
                overlaying='y',
                side='right'
            )
        )
    
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
    
    # Add budget component if available
    if budget_col and 'budget' in forecast.columns:
        components.append('budget')
    
    valid_components = [c for c in components if c in forecast.columns]
    
    components_path = None
    
    if valid_components:
        fig_comp = go.Figure()
        
        # Special styling for budget component
        for component in valid_components:
            if component == 'budget':
                fig_comp.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast[component],
                    mode='lines',
                    name='Budget Effect',
                    line=dict(color='green', width=2)
                ))
            else:
                fig_comp.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast[component],
                    mode='lines',
                    name=component.capitalize()  # Capitalize component names
                ))
        
        fig_comp.update_layout(
            title=f'{metric} Components',
            xaxis_title='Date',
            yaxis_title='Effect Value',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add explanation annotation for budget effect
        if 'budget' in valid_components:
            # Calculate average effect
            avg_effect = forecast['budget'].mean()
            effect_direction = "positive" if avg_effect > 0 else "negative" if avg_effect < 0 else "neutral"
            
            fig_comp.add_annotation(
                x=0.5,
                y=-0.15,
                xref="paper",
                yref="paper",
                text=f"Budget Effect: This shows how changes in budget influence {metric}.<br>The effect is {effect_direction} (avg: {avg_effect:.2f}).",
                showarrow=False,
                font=dict(size=10),
                bordercolor="#c7c7c7",
                borderwidth=1,
                borderpad=4,
                bgcolor="#f9f9f9",
                opacity=0.8
            )
        
        components_id = f"{metric}_components_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        components_path = f'static/plots/{components_id}.html'
        pyo.plot(fig_comp, filename=components_path, auto_open=False)
    
    return plot_path.replace('static/', ''), components_path.replace('static/', '') if components_path else None