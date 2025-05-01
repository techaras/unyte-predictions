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
    
    // Add formatting for budget inputs
    document.addEventListener('focus', function(e) {
        if (e.target.classList.contains('budget-input')) {
            // Remove commas on focus to allow editing
            e.target.value = e.target.value.replace(/,/g, '');
        }
    }, true);
    
    document.addEventListener('blur', function(e) {
        if (e.target.classList.contains('budget-input')) {
            // Add commas on blur
            let value = parseInt(e.target.value.replace(/,/g, ''), 10) || 0;
            e.target.value = value.toLocaleString();
        }
    }, true);
    
    // Format budget inputs on initial load
    document.querySelectorAll('.budget-input').forEach(input => {
        let value = parseInt(input.value.replace(/,/g, ''), 10) || 0;
        input.value = value.toLocaleString();
    });
});
