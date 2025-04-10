// Track if total budget is locked (default: true)
let isTotalBudgetLocked = true;

// Function to update displayed budget
function updateBudgetDisplay(forecastId, newBudget) {
    const displayEl = document.getElementById(`budget-display-${forecastId}`);
    const inputEl = document.getElementById(`budget-input-${forecastId}`);
    
    if (displayEl) {
        displayEl.textContent = formatCurrency(newBudget);
    }
    
    if (inputEl) {
        // Update the input value but only if it's not currently being edited
        if (inputEl.style.display === 'none') {
            inputEl.value = newBudget.toFixed(2);
        }
    }
}

// Function to update total budget display
function updateTotalBudgetDisplay(impactData) {
    const totalBudget = impactData.forecasts.reduce((sum, forecast) => sum + forecast.budget, 0);
    
    // Update the display element
    const totalBudgetDisplay = document.getElementById('total-budget-display');
    if (totalBudgetDisplay) {
        totalBudgetDisplay.textContent = formatCurrency(totalBudget).substring(1); // Remove $ as it's shown separately
    }
    
    // Update the input value but only if it's not currently being edited
    const totalBudgetInput = document.getElementById('total-budget-input');
    if (totalBudgetInput && totalBudgetInput.style.display === 'none') {
        totalBudgetInput.value = totalBudget.toFixed(2);
    }
}

// Function to handle budget distribution when in locked mode
function distributeBudgetChange(impactData, changedForecastId, budgetDelta) {
    // Skip distribution if not in locked mode
    if (!isTotalBudgetLocked) return;
    
    // Get all forecasts except the one that was changed
    const otherForecasts = impactData.forecasts.filter(f => f.id !== changedForecastId);
    
    // Calculate total budget of other forecasts
    const otherBudgetsTotal = otherForecasts.reduce((sum, f) => sum + f.budget, 0);
    
    // If there are no other forecasts or their total is zero, we can't distribute
    if (otherForecasts.length === 0 || otherBudgetsTotal <= 0) return;
    
    // Negative delta to distribute (if budget increased, others decrease)
    const deltaToDistribute = -budgetDelta;
    
    // Calculate and apply new budgets for other forecasts proportionally
    otherForecasts.forEach(forecast => {
        // Calculate proportion of this forecast relative to other forecasts
        const proportion = forecast.budget / otherBudgetsTotal;
        
        // Calculate this forecast's share of the delta
        const forecastDelta = deltaToDistribute * proportion;
        
        // Calculate new budget (allowing it to go to 0)
        let newBudget = Math.max(forecast.budget + forecastDelta, 0);
        
        // Update budget display
        updateBudgetDisplay(forecast.id, newBudget);
        
        // Calculate and update percentage change
        const changePercent = ((newBudget - forecast.original_budget) / forecast.original_budget) * 100;
        
        // Update slider position
        const slider = document.getElementById(`slider-${forecast.id}`);
        if (slider) {
            slider.value = getSliderValueFromChange(changePercent);
        }
    });
}

// Set up budget editing functionality
function setupBudgetEditing(impactData) {
    // Budget lock toggle handler
    const budgetLockToggle = document.getElementById('budget-lock-toggle');
    if (budgetLockToggle) {
        const toggleLabel = budgetLockToggle.closest('.budget-mode-toggle').querySelector('.toggle-label');
        
        budgetLockToggle.addEventListener('change', function() {
            isTotalBudgetLocked = this.checked;
            toggleLabel.textContent = isTotalBudgetLocked ? 'Budget Locked' : 'Budget Flexible';
        });
    }
    
    // Set up total budget editing
    const totalBudgetValueElement = document.getElementById('total-budget-value');
    if (totalBudgetValueElement) {
        const totalBudgetDisplay = document.getElementById('total-budget-display');
        const totalBudgetInput = document.getElementById('total-budget-input');
        
        // Make the display clickable to reveal the input
        if (totalBudgetDisplay && totalBudgetInput) {
            totalBudgetDisplay.addEventListener('click', function() {
                totalBudgetDisplay.style.display = 'none';
                totalBudgetInput.style.display = 'inline-block';
                totalBudgetInput.focus();
                totalBudgetInput.select();
            });
            
            // Handle input blur to update values
            totalBudgetInput.addEventListener('blur', function() {
                // Hide input, show display
                totalBudgetInput.style.display = 'none';
                totalBudgetDisplay.style.display = 'inline-block';
                
                // Get the new total budget value
                const newTotalBudget = parseCurrency(totalBudgetInput.value);
                totalBudgetDisplay.textContent = formatCurrency(newTotalBudget).substring(1); // Remove $ as it's shown separately
                
                // Calculate current total budget
                const currentTotalBudget = impactData.forecasts.reduce((sum, forecast) => sum + forecast.budget, 0);
                
                // Skip if no change or invalid value
                if (newTotalBudget === currentTotalBudget || newTotalBudget <= 0) {
                    return;
                }
                
                // Force budget lock mode when manually adjusting total
                if (!isTotalBudgetLocked && budgetLockToggle) {
                    budgetLockToggle.checked = true;
                    isTotalBudgetLocked = true;
                    const toggleLabel = budgetLockToggle.closest('.budget-mode-toggle').querySelector('.toggle-label');
                    toggleLabel.textContent = 'Budget Locked';
                }
                
                // Calculate adjustment factor
                const adjustmentFactor = newTotalBudget / currentTotalBudget;
                
                // Create changes object with percentage changes for all forecasts
                const changes = {};
                impactData.forecasts.forEach(forecast => {
                    // Calculate percentage change for each forecast
                    const changePercent = (forecast.budget * adjustmentFactor - forecast.original_budget) / 
                                        forecast.original_budget * 100;
                    changes[forecast.id] = changePercent;
                    
                    // Update the slider position
                    const slider = document.getElementById(`slider-${forecast.id}`);
                    if (slider) {
                        slider.value = getSliderValueFromChange(changePercent);
                    }
                });
                
                // Simulate budget changes
                simulateBudgetChanges(impactData, changes);
            });
            
            // Handle enter key on total budget input
            totalBudgetInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    this.blur();
                }
            });
        }
    }
    
    // Set up individual budget editing
    document.querySelectorAll('.budget-value').forEach(budgetValueEl => {
        const forecastId = budgetValueEl.id.replace('budget-', '');
        const forecast = impactData.forecasts.find(f => f.id === forecastId);
        
        if (forecast) {
            // Get the current budget value from the input
            const inputElement = budgetValueEl.querySelector('input');
            const currentValue = parseFloat(inputElement.value) || 0;
            
            // Replace with a better editable structure
            budgetValueEl.innerHTML = `
                <div class="budget-display" id="budget-display-${forecastId}">${formatCurrency(currentValue)}</div>
                <input type="text" class="budget-input" id="budget-input-${forecastId}" 
                       value="${currentValue.toFixed(2)}" style="display: none;"
                       data-original="${forecast.original_budget}">
            `;
            
            const displayEl = document.getElementById(`budget-display-${forecastId}`);
            const inputEl = document.getElementById(`budget-input-${forecastId}`);
            
            // Make the display clickable to reveal the input
            displayEl.addEventListener('click', function() {
                displayEl.style.display = 'none';
                inputEl.style.display = 'block';
                inputEl.focus();
                inputEl.select();
            });
            
            // Handle input blur to update values
            inputEl.addEventListener('blur', function() {
                // Hide input, show display
                inputEl.style.display = 'none';
                displayEl.style.display = 'block';
                
                // Get the new value
                const newValue = parseCurrency(inputEl.value);
                displayEl.textContent = formatCurrency(newValue);
                
                // Find the forecast
                const forecast = impactData.forecasts.find(f => f.id === forecastId);
                if (forecast) {
                    const oldBudget = forecast.budget;
                    const budgetDelta = newValue - oldBudget;
                    
                    // In locked mode, distribute the change to other budgets
                    if (isTotalBudgetLocked) {
                        distributeBudgetChange(impactData, forecastId, budgetDelta);
                    }
                    
                    // Calculate percentage change
                    const originalValue = parseFloat(inputEl.getAttribute('data-original'));
                    const changePercent = ((newValue - originalValue) / originalValue) * 100;
                    
                    // Update the slider
                    const slider = document.getElementById(`slider-${forecastId}`);
                    if (slider) {
                        slider.value = getSliderValueFromChange(changePercent);
                    }
                    
                    // Create changes object
                    let changes = {};
                    
                    if (isTotalBudgetLocked) {
                        // Get changes for all forecasts
                        impactData.forecasts.forEach(f => {
                            if (f.id === forecastId) {
                                changes[f.id] = changePercent;
                            } else {
                                // For others, calculate from current display
                                const displayEl = document.getElementById(`budget-display-${f.id}`);
                                if (displayEl) {
                                    const currentBudget = parseCurrency(displayEl.textContent);
                                    const fChangePercent = ((currentBudget - f.original_budget) / f.original_budget) * 100;
                                    changes[f.id] = fChangePercent;
                                }
                            }
                        });
                    } else {
                        // Just the changed forecast
                        changes[forecastId] = changePercent;
                    }
                    
                    // Simulate budget changes
                    simulateBudgetChanges(impactData, changes);
                }
            });
            
            // Handle enter key
            inputEl.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    this.blur();
                }
            });
        }
    });
}

// Set up slider event listeners
function setupSliders(impactData) {
    document.querySelectorAll('.slider').forEach(slider => {
        const forecastId = slider.id.replace('slider-', '');
        
        slider.addEventListener('input', function() {
            // Get the raw value from the slider
            const sliderValue = parseInt(this.value);
            
            // Convert to the business logic range (-50% to +100%)
            const adjustedChangePercent = getAdjustedBudgetChange(sliderValue);
            
            // Find the forecast in the data
            const forecast = impactData.forecasts.find(f => f.id === forecastId);
            if (forecast) {
                // Calculate new budget based on original budget
                const oldBudget = forecast.budget;
                const newBudget = forecast.original_budget * (1 + adjustedChangePercent/100);
                const budgetDelta = newBudget - oldBudget;
                
                // Update the displayed budget immediately for responsive UI
                updateBudgetDisplay(forecastId, newBudget);
                
                // In locked mode, distribute the change to other budgets on real-time dragging
                if (isTotalBudgetLocked) {
                    distributeBudgetChange(impactData, forecastId, budgetDelta);
                }
            }
        });
        
        slider.addEventListener('change', function() {
            // This fires when the user releases the slider
            const sliderValue = parseInt(this.value);
            
            // Convert to the business logic range (-50% to +100%)
            const adjustedChangePercent = getAdjustedBudgetChange(sliderValue);
            
            // Create changes object based on mode
            let changes = {};
            
            if (isTotalBudgetLocked) {
                // Get changes for all forecasts
                impactData.forecasts.forEach(f => {
                    if (f.id === forecastId) {
                        changes[f.id] = adjustedChangePercent;
                    } else {
                        // For others, get current slider value
                        const fSlider = document.getElementById(`slider-${f.id}`);
                        if (fSlider) {
                            const sliderVal = parseInt(fSlider.value);
                            changes[f.id] = getAdjustedBudgetChange(sliderVal);
                        }
                    }
                });
            } else {
                // Just the changed forecast
                changes[forecastId] = adjustedChangePercent;
            }
            
            // Send to server for simulation
            simulateBudgetChanges(impactData, changes);
        });
    });
}