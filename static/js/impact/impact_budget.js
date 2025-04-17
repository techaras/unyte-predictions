// Function to update budget and redistribute the difference to other forecasts
function updateBudget(input) {
    const forecastId = input.dataset.forecastId;

    // 1. Parse the user’s input (default 0) and compute the current total budget
    let newValue = parseInt(input.value, 10) || 0;
    const totalBudget = impactData.forecasts.reduce((sum, f) => {
        if (f.budget && f.budget.value != null) {
            return sum + Math.floor(parseFloat(f.budget.value));
        }
        return sum;
    }, 0);

    // 2. Clamp between 0 and totalBudget, and write it back to the input
    newValue = Math.max(0, Math.min(newValue, totalBudget));
    input.value = newValue;

    // 3. Now proceed as before
    const forecast = impactData.forecasts.find(f => f.id === forecastId);
    if (!forecast || !forecast.budget) {
        console.error('Forecast or budget not found');
        return;
    }

    const previousValue = parseFloat(forecast.budget.value);
    const difference = previousValue - newValue;

    // No meaningful change?
    if (Math.abs(difference) < 0.01) return;

    const otherForecasts = impactData.forecasts.filter(f =>
        f.id !== forecastId && f.budget && f.budget.value
    );

    // If it’s the only one, just set and exit
    if (otherForecasts.length === 0) {
        forecast.budget.value = newValue;
        updateAggregateBudget();
        return;
    }

    // Sum of the others
    const otherForecastsSum = otherForecasts.reduce((sum, f) =>
        sum + parseFloat(f.budget.value), 0
    );

    // Update this forecast
    forecast.budget.value = newValue;

    // Proportionally redistribute the difference
    otherForecasts.forEach(f => {
        const proportion = parseFloat(f.budget.value) / otherForecastsSum;
        const oldBudget = parseFloat(f.budget.value);
        const updatedBudget = oldBudget + (difference * proportion);
        f.budget.value = updatedBudget;

        // Reflect in any visible input
        const inputField = document.querySelector(
          `.budget-input[data-forecast-id="${f.id}"]`
        );
        if (inputField) {
            inputField.value = Math.floor(updatedBudget);
        }
    });

    // Finally, refresh the total (it stays constant)
    updateAggregateBudget();
}

// Store original budget values for reset functionality
function storeOriginalBudgets() {
    if (!impactData || !impactData.forecasts) return;
    
    impactData.originalBudgets = {};
    
    impactData.forecasts.forEach(forecast => {
        if (forecast.budget && forecast.budget.value) {
            // Store the original values in a separate object to prevent accidental modification
            impactData.originalBudgets[forecast.id] = parseFloat(forecast.budget.value);
        }
    });
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
            forecast.budget.value = originalValue;
            
            // Update the input field if it exists
            const inputField = document.querySelector(`.budget-input[data-forecast-id="${forecast.id}"]`);
            if (inputField) {
                inputField.value = Math.floor(originalValue);
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

// Make the functions available globally
window.updateBudget = updateBudget;
window.updateAggregateBudget = updateAggregateBudget;
window.resetBudgets = resetBudgets;
window.storeOriginalBudgets = storeOriginalBudgets;