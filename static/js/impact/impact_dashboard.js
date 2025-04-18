// Global impact data
let impactData = {};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Get the impact data from the page
    impactData = JSON.parse(document.getElementById('impact-data-json').textContent);
    
    // Initialize date range display
    updateDateRangeDisplay(impactData);
    
    // Calculate and display aggregate budget
    updateAggregateBudget();
    
    // Store original values for budget and metrics
    storeOriginalValues();
    
    // Initialize reset button
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetBudgets);
    }
    
    // Setup cleanup handler
    window.addEventListener('beforeunload', performCleanup);
});
