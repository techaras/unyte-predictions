// Add this temporary debugging function at the top
function debugAvailableMetrics() {
    console.log('=== DEBUGGING AVAILABLE METRICS ===');
    if (!impactData || !impactData.forecasts) {
        console.log('No impact data or forecasts found');
        return;
    }
    
    impactData.forecasts.forEach((forecast, index) => {
        console.log(`Forecast ${index}: ${forecast.title}`);
        console.log('Metrics:');
        forecast.metrics.forEach(metric => {
            console.log(`  - ${metric.name} (lowercase: ${metric.name.toLowerCase()})`);
        });
    });
    console.log('=== END DEBUG ===');
}

// Replace the calculateAggregatedMetrics function with this updated version
function calculateAggregatedMetrics() {
    if (!impactData || !impactData.forecasts) return;
    
    const insights = [];
    
    // Collect all conversions and clicks across all forecasts first
    let totalWebsitePurchases = { current: 0, simulated: 0 };
    let totalAllConversions = { current: 0, simulated: 0 };
    let totalLinkClicks = { current: 0, simulated: 0 };
    let totalClicks = { current: 0, simulated: 0 };
    
    impactData.forecasts.forEach(forecast => {
        // Check for Website Purchase (with variations)
        const websitePurchase = forecast.metrics.find(m => {
            const nameLower = m.name.toLowerCase();
            return nameLower.includes('website purchase') || nameLower.includes('website purchases');
        });
        
        if (websitePurchase) {
            totalWebsitePurchases.current += parseFloat(websitePurchase.current);
            totalWebsitePurchases.simulated += parseFloat(websitePurchase.simulated);
        }
        
        // Check for All Conv. (with variations)
        const allConv = forecast.metrics.find(m => {
            const nameLower = m.name.toLowerCase();
            return nameLower.includes('all conv') || nameLower === 'all conv';
        });
        
        if (allConv) {
            totalAllConversions.current += parseFloat(allConv.current);
            totalAllConversions.simulated += parseFloat(allConv.simulated);
        }
        
        // Check for Link Clicks
        const linkClicks = forecast.metrics.find(m => {
            const nameLower = m.name.toLowerCase();
            return nameLower.includes('link clicks');
        });
        
        if (linkClicks) {
            totalLinkClicks.current += parseFloat(linkClicks.current);
            totalLinkClicks.simulated += parseFloat(linkClicks.simulated);
        }
        
        // Check for Clicks
        const clicks = forecast.metrics.find(m => {
            const nameLower = m.name.toLowerCase();
            return nameLower === 'clicks' || nameLower === 'total clicks';
        });
        
        if (clicks) {
            totalClicks.current += parseFloat(clicks.current);
            totalClicks.simulated += parseFloat(clicks.simulated);
        }
    });
    
    // Create aggregated insights
    if (totalWebsitePurchases.current > 0 || totalAllConversions.current > 0) {
        insights.push({
            forecastId: 'aggregate-conversions',
            forecastTitle: 'All Campaigns',
            type: 'conversions',
            name: 'Total Conversions (Website Purchases + All Conv.)',
            current: totalWebsitePurchases.current + totalAllConversions.current,
            simulated: totalWebsitePurchases.simulated + totalAllConversions.simulated
        });
    }
    
    if (totalLinkClicks.current > 0 || totalClicks.current > 0) {
        insights.push({
            forecastId: 'aggregate-clicks',
            forecastTitle: 'All Campaigns',
            type: 'clicks',
            name: 'Total Clicks (Link Clicks + Clicks)',
            current: totalLinkClicks.current + totalClicks.current,
            simulated: totalLinkClicks.simulated + totalClicks.simulated
        });
    }
    
    console.log('Aggregated insights:', insights);
    displayAggregatedMetrics(insights);
}

// Function to display aggregated metrics
function displayAggregatedMetrics(insights) {
    const insightsGrid = document.getElementById('insights-grid');
    if (!insightsGrid) return;
    
    insightsGrid.innerHTML = ''; // Clear existing content
    
    if (insights.length === 0) {
        insightsGrid.innerHTML = '<p class="no-insights">No aggregatable metrics found</p>';
        return;
    }
    
    insights.forEach(insight => {
        const impactPercent = ((insight.simulated - insight.current) / insight.current) * 100;
        const impactClass = impactPercent > 0 ? 'impact-positive' : 
                           impactPercent < 0 ? 'impact-negative' : 'impact-neutral';
        
        const insightCard = document.createElement('div');
        insightCard.className = 'insight-card';
        insightCard.innerHTML = `
            <div class="insight-header">
                <h4>${insight.forecastTitle}</h4>
                <span class="insight-type">${insight.name}</span>
            </div>
            <div class="insight-metrics">
                <div class="metric-value">
                    <span class="metric-label">Current:</span>
                    <span class="metric-number">${Math.round(insight.current).toLocaleString()}</span>
                </div>
                <div class="metric-value">
                    <span class="metric-label">Simulated:</span>
                    <span class="metric-number">${Math.round(insight.simulated).toLocaleString()}</span>
                </div>
                <div class="metric-value impact">
                    <span class="metric-label">Impact:</span>
                    <span class="metric-number ${impactClass}">${impactPercent.toFixed(1)}%</span>
                </div>
            </div>
        `;
        
        insightsGrid.appendChild(insightCard);
    });
}

// Function to refresh insights when budget changes
function refreshInsights() {
    calculateAggregatedMetrics();
}

// Initialize insights on page load
document.addEventListener('DOMContentLoaded', function() {
    calculateAggregatedMetrics();
});