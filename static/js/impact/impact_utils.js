// Format currency with proper formatting
function formatCurrency(value) {
    return '$' + parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Parse currency string to number
function parseCurrency(value) {
    return parseFloat(value.replace(/[^0-9.-]+/g, '')) || 0;
}

// Function to update date range display
function updateDateRangeDisplay(impactData) {
    const dateRangeElement = document.getElementById('date-range-text');
    if (!dateRangeElement) return;
    
    // Get date range from the impact data
    let startDate = new Date();
    let endDate = new Date();
    endDate.setDate(startDate.getDate() + 90); // Default 90-day window
    
    // Try to get the date range from the impact data
    if (impactData.date_range) {
        startDate = new Date(impactData.date_range.start);
        endDate = new Date(impactData.date_range.end);
    } else if (impactData.forecasts && impactData.forecasts.length > 0) {
        // Try to get from the first forecast as fallback
        const firstForecast = impactData.forecasts[0];
        if (firstForecast.date_range) {
            startDate = new Date(firstForecast.date_range.start);
            endDate = new Date(firstForecast.date_range.end);
        }
    }
    
    // Format dates
    const formatOptions = { year: 'numeric', month: 'short', day: 'numeric' };
    const startFormatted = startDate.toLocaleDateString('en-US', formatOptions);
    const endFormatted = endDate.toLocaleDateString('en-US', formatOptions);
    
    // Update the text
    dateRangeElement.textContent = `${startFormatted} - ${endFormatted}`;
}

// Function to convert from slider scale (-100% to +100%) to business logic scale (-50% to +100%)
function getAdjustedBudgetChange(sliderValue) {
    // For positive values (0 to 100), keep as is
    if (sliderValue >= 0) {
        return sliderValue;
    } else {
        // For negative values, scale -100% to -50%
        // (multiply by 0.5 to convert -100 to -50)
        return sliderValue * 0.5;
    }
}

// Function to convert from business logic scale (-50% to +100%) to slider scale (-100% to +100%)
function getSliderValueFromChange(changePercent) {
    if (changePercent >= 0) {
        return changePercent; // Positive values map directly
    } else {
        return changePercent * 2; // Scale -50% to -100% for slider
    }
}