document.addEventListener('DOMContentLoaded', function() {
    // File input styling
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('file-name');
    
    if (fileInput && fileName) {
        fileInput.addEventListener('change', function() {
            const selectedFile = this.files[0];
            if (selectedFile) {
                fileName.textContent = selectedFile.name;
            } else {
                fileName.textContent = '';
            }
        });
    }
    
    // Select all/none buttons for metrics
    const selectAll = document.getElementById('select-all');
    const selectNone = document.getElementById('select-none');
    
    if (selectAll) {
        selectAll.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('input[name="metrics"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    }
    
    if (selectNone) {
        selectNone.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('input[name="metrics"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }
    
    // Form validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const forecastPeriod = document.getElementById('forecast_period');
            
            if (forecastPeriod && (forecastPeriod.value < 1 || forecastPeriod.value > 365)) {
                e.preventDefault();
                alert('Forecast period must be between 1 and 365 days');
                return false;
            }
            
            // For metrics selection page
            const checkboxes = document.querySelectorAll('input[name="metrics"]');
            if (checkboxes.length > 0) {
                let atLeastOneSelected = false;
                checkboxes.forEach(checkbox => {
                    if (checkbox.checked) {
                        atLeastOneSelected = true;
                    }
                });
                
                if (!atLeastOneSelected) {
                    e.preventDefault();
                    alert('Please select at least one metric to forecast');
                    return false;
                }
            }
        });
    }
    
    // Format numbers with commas
    function formatNumber(num) {
        return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    
    // Budget calculation functionality
    function calculateBudget(forecastDays) {
        // Get the daily average from the server-provided data or default to 0
        const budgetData = window.budgetData || { dailyAverage: 0, currency: '£' };
        const dailyAverage = parseFloat(budgetData.dailyAverage) || 0;
        const currency = budgetData.currency || '£';
        
        // Calculate total budget
        const totalBudget = dailyAverage * forecastDays;
        
        // Update the UI elements
        const budgetPeriodText = document.getElementById('budget-period-text');
        const budgetCurrency = document.getElementById('budget-currency');
        const budgetInput = document.getElementById('budget-input');
        const dailyBudgetText = document.getElementById('daily-budget-text');
        const estimatedBudget = document.getElementById('estimated_budget');
        
        if (budgetPeriodText) {
            budgetPeriodText.textContent = 
                `Budget will be distributed across the ${forecastDays}-day forecast period`;
        }
        if (budgetCurrency) {
            budgetCurrency.textContent = currency;
        }
        if (budgetInput) {
            // Set the value for the editable input
            budgetInput.value = formatNumber(totalBudget);
        }
        if (dailyBudgetText) {
            dailyBudgetText.textContent = 
                `~${currency}${formatNumber(dailyAverage)} per day based on ${forecastDays}-day period`;
        }
        if (estimatedBudget) {
            estimatedBudget.value = totalBudget;
        }
    }
    
    // Setup date picker and budget calculation
    const campaignEndDateInput = document.getElementById('campaign_end_date');
    const forecastPeriodInput = document.getElementById('forecast_period');
    const lastCsvDateInput = document.getElementById('last_csv_date');
    const daysCountSpan = document.getElementById('days-count');
    const csvLastDateSpan = document.getElementById('csv-last-date');
    
    if (campaignEndDateInput && forecastPeriodInput && lastCsvDateInput) {
        // Format last CSV date for display
        const formatDate = (date) => {
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            return `${day}/${month}/${year}`;
        };
        
        // Get the last date from the CSV
        const lastCsvDateStr = lastCsvDateInput.value;
        const lastCsvDate = new Date(lastCsvDateStr);
        
        // Set CSV last date in the display if the element exists
        if (csvLastDateSpan) {
            csvLastDateSpan.textContent = formatDate(lastCsvDate);
        }
        
        // Set default end date (30 days from last CSV date)
        const defaultEndDate = new Date(lastCsvDate);
        defaultEndDate.setDate(lastCsvDate.getDate() + 30);
        
        // Format the date for the input value (YYYY-MM-DD)
        const formatDateForInput = (date) => {
            return date.toISOString().split('T')[0];
        };
        
        // Set default date if it hasn't been set already
        if (!campaignEndDateInput.value) {
            campaignEndDateInput.value = formatDateForInput(defaultEndDate);
        }
        
        // Update days count and budget when date changes
        campaignEndDateInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const diffTime = Math.abs(selectedDate - lastCsvDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            // Update the forecast period
            if (daysCountSpan) {
                daysCountSpan.textContent = diffDays;
            }
            forecastPeriodInput.value = diffDays;
            
            // Update the budget calculation
            calculateBudget(diffDays);
        });
        
        // Initial calculation with default value
        const initialDays = parseInt(forecastPeriodInput.value) || 30;
        calculateBudget(initialDays);
    }
    
    // Handle editable budget input
    const budgetInput = document.getElementById('budget-input');
    if (budgetInput) {
        // Add event listener for when the user edits the budget
        budgetInput.addEventListener('input', function() {
            // Remove any commas that might be in the input
            const rawValue = this.value.replace(/,/g, '');
            // Parse the value
            let totalBudget = parseFloat(rawValue) || 0;
            
            // Update the hidden field
            const estimatedBudget = document.getElementById('estimated_budget');
            if (estimatedBudget) {
                estimatedBudget.value = totalBudget;
            }
            
            // Update the daily budget display
            const forecastPeriodInput = document.getElementById('forecast_period');
            const forecastDays = parseInt(forecastPeriodInput.value) || 30;
            const dailyAverage = totalBudget / forecastDays;
            
            const dailyBudgetText = document.getElementById('daily-budget-text');
            const budgetCurrency = document.getElementById('budget-currency');
            const currency = budgetCurrency ? budgetCurrency.textContent : '£';
            
            if (dailyBudgetText) {
                dailyBudgetText.textContent = 
                    `~${currency}${formatNumber(dailyAverage)} per day based on ${forecastDays}-day period`;
            }
        });
        
        // Add formatting when the field loses focus
        budgetInput.addEventListener('blur', function() {
            const rawValue = this.value.replace(/,/g, '');
            const totalBudget = parseFloat(rawValue) || 0;
            this.value = formatNumber(totalBudget);
        });
        
        // Remove formatting when the field gets focus
        budgetInput.addEventListener('focus', function() {
            const rawValue = this.value.replace(/,/g, '');
            const totalBudget = parseFloat(rawValue) || 0;
            this.value = totalBudget.toFixed(2);
        });
    }
});