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