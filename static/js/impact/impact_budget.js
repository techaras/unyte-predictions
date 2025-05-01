// Store original budget and metric values for calculations
function storeOriginalValues() {
    if (!impactData || !impactData.forecasts) return;
    
    // Store original budgets
    impactData.originalBudgets = {};
    
    // Store original metric values
    impactData.originalMetrics = {};
    
    impactData.forecasts.forEach(forecast => {
        // Store original budget
        if (forecast.budget && forecast.budget.value !== null && forecast.budget.value !== undefined) {
            impactData.originalBudgets[forecast.id] = parseFloat(forecast.budget.value);
        }
        
        // Store original metric values
        if (forecast.metrics && forecast.metrics.length > 0) {
            impactData.originalMetrics[forecast.id] = forecast.metrics.map(metric => ({
                name: metric.name,
                value: parseFloat(metric.current)
            }));
        }
    });
}

// Function to update budget and redistribute the difference to other forecasts
function updateBudget(input) {
    const forecastId = input.dataset.forecastId;

    // 1. Parse the user's input (default 0) and compute the current total budget
    let newValue = parseInt(input.value.replace(/,/g, ''), 10) || 0;
    const totalBudget = impactData.forecasts.reduce((sum, f) => {
        if (f.budget && f.budget.value != null) {
            return sum + Math.floor(parseFloat(f.budget.value));
        }
        return sum;
    }, 0);

    // 2. Clamp between 0 and totalBudget, and write it back to the input
    newValue = Math.max(0, Math.min(newValue, totalBudget));
    input.value = newValue.toLocaleString();

    // 3. Locate this forecast entry
    const forecast = impactData.forecasts.find(f => f.id === forecastId);
    if (!forecast || !forecast.budget) {
        console.error('Forecast or budget not found');
        return;
    }

    const previousValue = parseFloat(forecast.budget.value);
    const difference = previousValue - newValue;

    // No meaningful change?
    if (Math.abs(difference) < 0.01) return;

    // 4. Include zero‑value buckets in the pool
    const otherForecasts = impactData.forecasts.filter(f =>
        f.id !== forecastId &&
        f.budget &&
        f.budget.value != null      // allow 0
    );

    // 5. Sum of the others
    const otherForecastsSum = otherForecasts.reduce((sum, f) =>
        sum + parseFloat(f.budget.value), 0
    );

    // 6. If everyone else is at zero, give the full difference to the first one
    if (otherForecastsSum === 0 && otherForecasts.length > 0) {
        // Save the old budget for the first other forecast
        const f0 = otherForecasts[0];
        const f0OldBudget = parseFloat(f0.budget.value);
        
        // update this forecast
        forecast.budget.value = newValue;
        
        // hand the entire difference to the first other forecast
        f0.budget.value = f0OldBudget + difference;

        // reflect in the UI with comma formatting
        const input0 = document.querySelector(
            `.budget-input[data-forecast-id="${f0.id}"]`
        );
        if (input0) input0.value = Math.floor(f0.budget.value).toLocaleString();
        
        // Recalculate metrics for both forecasts
        recalculateMetricsForBudgetChange(forecastId, previousValue, newValue);
        recalculateMetricsForBudgetChange(f0.id, f0OldBudget, f0.budget.value);
        
        updateAggregateBudget();
        return;
    }

    // 7. Otherwise, proceed with proportional redistribution
    //    first update this forecast
    forecast.budget.value = newValue;
    
    // Recalculate metrics for the current forecast
    recalculateMetricsForBudgetChange(forecastId, previousValue, newValue);

    // Store old budgets for other forecasts before updating
    const oldBudgets = {};
    otherForecasts.forEach(f => {
        oldBudgets[f.id] = parseFloat(f.budget.value);
    });

    // Now update other forecasts with proportional redistribution
    otherForecasts.forEach(f => {
        const oldBudget = oldBudgets[f.id];
        const proportion = oldBudget / otherForecastsSum;
        const updatedBudget = oldBudget + (difference * proportion);
        f.budget.value = updatedBudget;

        // reflect in the UI with comma formatting
        const inputField = document.querySelector(
            `.budget-input[data-forecast-id="${f.id}"]`
        );
        if (inputField) {
            inputField.value = Math.floor(updatedBudget).toLocaleString();
        }
        
        // Recalculate metrics for this forecast
        recalculateMetricsForBudgetChange(f.id, oldBudget, updatedBudget);
    });

    // 8. Finally, refresh the total (it stays constant)
    updateAggregateBudget();
}

// Store original budget values for reset functionality
function storeOriginalBudgets() {
    console.log("=== STORING ORIGINAL BUDGETS ===");
    
    if (!impactData || !impactData.forecasts) {
        console.error("No impact data or forecasts found");
        return;
    }
    
    impactData.originalBudgets = {};
    
    impactData.forecasts.forEach(forecast => {
        if (forecast.budget && forecast.budget.value !== null && forecast.budget.value !== undefined) {
            // Store the original values in a separate object to prevent accidental modification
            impactData.originalBudgets[forecast.id] = parseFloat(forecast.budget.value);
            console.log(`Stored original budget for ${forecast.id}: ${impactData.originalBudgets[forecast.id]}`);
        } else {
            console.log(`No budget found for forecast ${forecast.id}`);
        }
    });
    
    console.log("Original budgets stored:", impactData.originalBudgets);
}

// Reset all budgets to original values
function resetBudgets() {
    if (!impactData || !impactData.forecasts || !impactData.originalBudgets) {
        console.error('Cannot reset: original budget data not found');
        return;
    }
    
    // Get the reset button
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.classList.add('loading');
    }
    
    // Reset budgets to original values
    impactData.forecasts.forEach(forecast => {
        if (forecast.budget && impactData.originalBudgets[forecast.id] !== undefined) {
            const originalValue = impactData.originalBudgets[forecast.id];
            const currentValue = parseFloat(forecast.budget.value);
            
            // Only update if there's a change
            if (Math.abs(currentValue - originalValue) > 0.01) {
                forecast.budget.value = originalValue;
                
                // Update the input field if it exists
                const inputField = document.querySelector(`.budget-input[data-forecast-id="${forecast.id}"]`);
                if (inputField) {
                    inputField.value = Math.floor(originalValue);
                }
                
                // Reset metrics directly to original values
                if (impactData.originalMetrics && impactData.originalMetrics[forecast.id]) {
                    forecast.metrics.forEach(metric => {
                        const originalMetric = impactData.originalMetrics[forecast.id].find(m => m.name === metric.name);
                        if (originalMetric) {
                            metric.simulated = originalMetric.value;
                            metric.impact = 0; // Reset impact to zero
                        }
                    });
                    
                    // Update the UI
                    updateMetricDisplays(forecast.id, forecast.metrics);
                }
            }
        }
    });
    
    // Update the UI
    updateAggregateBudget();
    
    if (resetBtn) {
        setTimeout(() => {
            resetBtn.classList.remove('loading');
        }, 300);
    }
}

// Calculate and display the aggregate budget
function updateAggregateBudget() {
    // Get references to the DOM elements
    const currencyElement = document.getElementById('aggregate-budget-currency');
    const valueElement = document.getElementById('aggregate-budget-value');
    
    if (!currencyElement || !valueElement) {
        console.error('Aggregate budget elements not found');
        return;
    }
    
    // Default currency symbol (fallback)
    let currency = '£';
    
    // Calculate the total from the impact data
    let totalBudget = 0;
    let hasBudgetData = false;
    
    // Loop through all forecasts
    if (impactData && impactData.forecasts) {
        impactData.forecasts.forEach(forecast => {
            if (forecast.budget && forecast.budget.value) {
                // Add to the total using Math.floor to match |int filter behavior
                totalBudget += Math.floor(parseFloat(forecast.budget.value));
                
                // Use the currency from the data (take the first non-empty one)
                if (forecast.budget.currency && !hasBudgetData) {
                    currency = forecast.budget.currency;
                    hasBudgetData = true;
                }
            }
        });
    }
    
    // Update the DOM
    currencyElement.textContent = currency;
    valueElement.textContent = totalBudget.toLocaleString();
}

// Function to calculate slider position based on budget percentage
function updateSliderPosition(forecastId) {
    if (!impactData || !impactData.forecasts) return;
    
    // Calculate total budget
    const totalBudget = impactData.forecasts.reduce((sum, f) => {
        if (f.budget && f.budget.value != null) {
            return sum + parseFloat(f.budget.value);
        }
        return sum;
    }, 0);
    
    // Get the forecast
    const forecast = impactData.forecasts.find(f => f.id === forecastId);
    if (!forecast || !forecast.budget) return;
    
    // Calculate percentage
    let percentage = 0;
    if (totalBudget > 0) {
        percentage = (parseFloat(forecast.budget.value) / totalBudget) * 100;
    }
    
    // Update slider
    const slider = document.querySelector(`.budget-slider[data-forecast-id="${forecastId}"]`);
    if (slider) {
        slider.value = percentage;
    }
}

// Function to update all sliders
function updateAllSliders() {
    if (!impactData || !impactData.forecasts) return;
    
    impactData.forecasts.forEach(forecast => {
        updateSliderPosition(forecast.id);
    });
}

// Function to handle slider changes
function handleSliderChange(slider) {
    const forecastId = slider.dataset.forecastId;
    const newPercentage = parseFloat(slider.value);
    
    // Find the forecast
    const forecast = impactData.forecasts.find(f => f.id === forecastId);
    if (!forecast || !forecast.budget) return;
    
    // Calculate total budget
    const totalBudget = impactData.forecasts.reduce((sum, f) => {
        if (f.budget && f.budget.value != null) {
            return sum + parseFloat(f.budget.value);
        }
        return sum;
    }, 0);
    
    // Calculate new budget value based on percentage
    const newBudgetValue = (newPercentage / 100) * totalBudget;
    
    // Update the input field
    const inputField = document.querySelector(`.budget-input[data-forecast-id="${forecastId}"]`);
    if (inputField) {
        inputField.value = Math.floor(newBudgetValue).toLocaleString();
        // Trigger the existing updateBudget function
        updateBudget(inputField);
    }
}

// Initialize sliders when the page loads
function initializeSliders() {
    // Add slider attributes to existing sliders
    document.querySelectorAll('.budget-slider').forEach(slider => {
        // Find the corresponding budget input
        const budgetCell = slider.closest('.budget-cell');
        if (budgetCell) {
            const budgetInput = budgetCell.querySelector('.budget-input');
            if (budgetInput) {
                const forecastId = budgetInput.dataset.forecastId;
                slider.setAttribute('data-forecast-id', forecastId);
                
                // Add event listener for changes
                slider.addEventListener('input', function() {
                    handleSliderChange(this);
                });
            }
        }
    });
    
    // Set initial slider positions
    updateAllSliders();
}

// Modify the existing updateBudget function to update sliders
const originalUpdateBudget = updateBudget;
updateBudget = function(input) {
    // Call the original function
    originalUpdateBudget(input);
    
    // Update all sliders after budget changes
    updateAllSliders();
};

// Modify the resetBudgets function to update sliders
const originalResetBudgets = resetBudgets;
resetBudgets = function() {
    // Call the original function
    originalResetBudgets();
    
    // Update all sliders after reset
    updateAllSliders();
};

// Add initialization to DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for the impact data to be loaded
    if (impactData && impactData.forecasts) {
        initializeSliders();
    } else {
        // If data isn't ready yet, wait for it
        const originalInit = window.onload;
        window.onload = function() {
            if (originalInit) originalInit();
            initializeSliders();
        };
    }
});

// Make the functions available globally
window.updateBudget = updateBudget;
window.updateAggregateBudget = updateAggregateBudget;
window.resetBudgets = resetBudgets;
window.storeOriginalBudgets = storeOriginalBudgets;