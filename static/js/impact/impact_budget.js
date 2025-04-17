// Function to update budget when changed
function updateBudget(input) {
    const forecastId = input.dataset.forecastId;
    const newValue = parseInt(input.value) || 0;
    
    // Update in the data structure
    const forecast = impactData.forecasts.find(f => f.id === forecastId);
    if (forecast && forecast.budget) {
        forecast.budget.value = newValue;
    }
    
    // Update aggregate budget
    updateAggregateBudget();
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