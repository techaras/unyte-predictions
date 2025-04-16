// Global impact data
let impactData = {};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Get the impact data from the page
    impactData = JSON.parse(document.getElementById('impact-data-json').textContent);
    
    // Initialize date range display
    updateDateRangeDisplay(impactData);
    
    // Setup cleanup handler
    window.addEventListener('beforeunload', performCleanup);
});

// Note: setupResetButton has been removed as it was primarily for budget functionality