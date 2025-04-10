// Global impact data
let impactData = {};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Get the impact data from the page
    impactData = JSON.parse(document.getElementById('impact-data-json').textContent);
    
    // Initialize date range display
    updateDateRangeDisplay(impactData);
    
    // Setup budget editing functionality
    setupBudgetEditing(impactData);
    
    // Setup sliders
    setupSliders(impactData);
    
    // Setup reset button
    setupResetButton();
    
    // Setup cleanup handler
    window.addEventListener('beforeunload', performCleanup);
});

// Setup reset button functionality
function setupResetButton() {
    const resetButton = document.getElementById('reset-btn');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            // Reset all sliders to 0
            document.querySelectorAll('.slider').forEach(slider => {
                slider.value = 0;
            });
            
            // Create an object with 0% change for all forecasts
            const changes = {};
            impactData.forecasts.forEach(forecast => {
                changes[forecast.id] = 0;
            });
            
            // Simulate with all zeros to reset
            simulateBudgetChanges(impactData, changes);
        });
    }
}