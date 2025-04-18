// Function to update metric displays
function updateMetricDisplays(forecastId, updatedMetrics) {
    const rows = document.querySelectorAll(`.forecast-row[data-forecast-id="${forecastId}"]`);
    
    rows.forEach(row => {
        const metricName = row.querySelector('[data-metric]').getAttribute('data-metric');
        const simulatedElement = row.querySelector(`.metric-simulated[data-metric="${metricName}"]`);
        const impactElement = row.querySelector(`.impact-value[data-metric="${metricName}"]`);
        
        const metricData = updatedMetrics.find(m => m.name === metricName);
        if (metricData && simulatedElement && impactElement) {
            // Update simulated value with appropriate formatting
            if (metricName === 'ROAS') {
                simulatedElement.textContent = parseFloat(metricData.simulated).toFixed(1);
            } else if (metricName === 'CTR' || metricName === 'Conversion Rate') {
                simulatedElement.textContent = parseFloat(metricData.simulated).toFixed(2);
            } else {
                simulatedElement.textContent = Math.round(parseFloat(metricData.simulated));
            }
            
            // Update impact value and color
            impactElement.textContent = `${metricData.impact.toFixed(1)}%`;
            
            // Remove all impact classes
            impactElement.classList.remove('impact-positive', 'impact-negative', 'impact-neutral');
            
            // Add appropriate impact class
            if (metricData.impact > 0) {
                impactElement.classList.add('impact-positive');
            } else if (metricData.impact < 0) {
                impactElement.classList.add('impact-negative');
            } else {
                impactElement.classList.add('impact-neutral');
            }
        }
    });
}

// Function to recalculate metrics based on budget changes
function recalculateMetricsForBudgetChange(forecastId, oldBudget, newBudget) {
    // Find the forecast
    const forecast = impactData.forecasts.find(f => f.id === forecastId);
    if (!forecast) return;
    
    // Ensure we have original metric values stored
    if (!impactData.originalMetrics || !impactData.originalMetrics[forecastId]) {
        console.error(`No original metrics found for forecast ${forecastId}`);
        return;
    }
    
    // Skip if new budget is invalid
    if (newBudget === null || newBudget === undefined || newBudget < 0) {
        newBudget = 0;
    }
    
    // Get original budget - this is our baseline for calculations
    const originalBudget = impactData.originalBudgets[forecastId] || 0;
    
    // Skip calculation if original budget was zero - can't proportionally scale from zero
    if (originalBudget <= 0) {
        console.warn(`Original budget for ${forecastId} is zero or negative. Can't calculate proportional metrics.`);
        return;
    }
    
    // Calculate the budget ratio compared to ORIGINAL budget (not previous budget)
    const budgetRatio = newBudget / originalBudget;
    
    // List of metrics that should scale with budget changes
    const scalableMetrics = [
        'clicks', 'link clicks', 'total clicks', 
        'conversions', 'all conv', 'conv', 'website purchases',
        'impressions', 'impr', 'imps',
        'spend', 'cost', 'amount spent', 'value', 'conv. value'
    ];
    
    // List of metrics that should NOT scale with budget (rates)
    const nonScalableMetrics = [
        'ctr', 'click through rate', 'click-through rate',
        'conversion rate', 'conv. rate', 'cr', 'cvr',
        'cpc', 'cost per click', 'avg. cpc', 'average cpc',
        'cpm', 'cost per mille', 'cost per thousand',
        'roas', 'roi'
    ];
    
    // Update each metric
    forecast.metrics.forEach(metric => {
        const metricNameLower = metric.name.toLowerCase();
        
        // Get the original metric value from our stored original metrics
        const originalMetricValue = impactData.originalMetrics[forecastId].find(
            m => m.name === metric.name
        )?.value;
        
        // Skip if no original value found
        if (originalMetricValue === undefined || originalMetricValue === null) {
            console.warn(`No original value found for metric ${metric.name}`);
            return;
        }
        
        let newValue, impactPercent;
        
        // Determine if this metric should scale with budget
        if (scalableMetrics.some(term => metricNameLower.includes(term))) {
            // Direct scaling for volume metrics using ORIGINAL values
            newValue = originalMetricValue * budgetRatio;
            impactPercent = (budgetRatio - 1) * 100;
        } else if (nonScalableMetrics.some(term => metricNameLower.includes(term))) {
            // No change for rate metrics - use original value
            newValue = originalMetricValue;
            impactPercent = 0;
        } else {
            // Default behavior for unknown metrics (assume they scale)
            newValue = originalMetricValue * budgetRatio;
            impactPercent = (budgetRatio - 1) * 100;
        }
        
        // Special case for ROAS - it tends to decrease slightly as budget increases
        if (metricNameLower === 'roas') {
            const elasticity = 0.05; // 5% reduction in efficiency for each doubling of budget
            const roasModifier = Math.pow(budgetRatio, -elasticity);
            newValue = originalMetricValue * roasModifier;
            impactPercent = ((roasModifier - 1) * 100);
        }
        
        // Update the metric object
        metric.simulated = newValue;
        metric.impact = impactPercent;
    });
    
    // Update the UI
    updateMetricDisplays(forecastId, forecast.metrics);
}

// Function to refresh metric data
async function refreshMetricData() {
    try {
        const response = await fetch('/impact/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error('Refresh failed');
        }
        
        // Update the impact data with the response
        const updatedData = await response.json();
        
        // Update our global data
        Object.assign(impactData, updatedData);
        
        // Update the UI with the new data
        updatedData.forecasts.forEach(forecast => {
            updateMetricDisplays(forecast.id, forecast.metrics);
        });
        
    } catch (error) {
        console.error('Error refreshing metric data:', error);
        alert('Failed to refresh metric data. Please try again.');
    }
}

// Function to handle cleanup when leaving the page
async function performCleanup() {
    try {
        // Send cleanup request to remove temporary files
        await fetch('/impact/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    } catch (error) {
        console.error('Error during cleanup:', error);
    }
}