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
    
    // Platform detection for the forecast title badge
    const adPlatformBadge = document.getElementById('ad-platform-badge');
    if (adPlatformBadge) {
        // Get the file format from server-side data
        const fileFormatSource = window.fileFormat ? window.fileFormat.source : 'unknown';
        
        let platformName = 'Unknown';
        let platformClass = 'platform-unknown';
        
        // Determine platform based on file format
        if (fileFormatSource === 'google_ads') {
            platformName = 'Google Ads';
            platformClass = 'platform-google';
        } else if (fileFormatSource === 'meta') {
            platformName = 'Meta Ads';
            platformClass = 'platform-meta';
        } else if (fileFormatSource === 'amazon') {
            platformName = 'Amazon Ads';
            platformClass = 'platform-amazon';
        }
        
        // Add the platform badge
        adPlatformBadge.className = `ad-platform-badge ${platformClass}`;
        adPlatformBadge.textContent = platformName;
    }

    // Pre-fill the forecast title with a smart default name
    const forecastTitleInput = document.getElementById('forecast_title');
    if (forecastTitleInput) {
        // Get the platform type
        const fileFormatSource = window.fileFormat ? window.fileFormat.source : 'unknown';
        let platformName = 'Campaign';
        
        if (fileFormatSource === 'google_ads') {
            platformName = 'Google Ads';
        } else if (fileFormatSource === 'meta') {
            platformName = 'Meta';
        } else if (fileFormatSource === 'amazon') {
            platformName = 'Amazon Ads';
        }
        
        // Get date information
        const lastCsvDateInput = document.getElementById('last_csv_date');
        let dateInfo = '';
        
        if (lastCsvDateInput && lastCsvDateInput.value) {
            const lastDate = new Date(lastCsvDateInput.value);
            // Format like "Feb 2025"
            dateInfo = lastDate.toLocaleDateString('en-US', {month: 'short', year: 'numeric'});
        } else {
            // Fallback to current month/year
            const currentDate = new Date();
            dateInfo = currentDate.toLocaleDateString('en-US', {month: 'short', year: 'numeric'});
        }
        
        // Try to extract campaign info from CSV filename
        const csvFileElement = document.querySelector('.column-select-form div[style*="cursor: default"]');
        let campaignInfo = '';
        
        if (csvFileElement) {
            const filename = csvFileElement.textContent.trim();
            // Extract campaign name patterns
            if (filename.includes('Madrid')) {
                campaignInfo = 'Madrid';
            } else if (filename.includes('Campaign')) {
                campaignInfo = 'Campaign';
            }
        }
        
        // Construct the title with available information
        let titleParts = [platformName];
        
        if (campaignInfo) {
            titleParts.push(campaignInfo);
        }
        
        titleParts.push(dateInfo);
        
        // Set the forecast title
        forecastTitleInput.value = titleParts.join(' - ');
    }
    
    // Select all/none buttons for metrics
    const selectAll = document.getElementById('select-all');
    const selectNone = document.getElementById('select-none');
    
    // The rest of your existing code continues here...
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
        const budgetData = window.budgetData || { dailyAverage: 0, currency: '£', isValid: false };
        const dailyAverage = parseFloat(budgetData.dailyAverage) || 0;
        const currency = '£';  // Always use '£'
        const isValidBudget = budgetData.isValid === true;
        
        // Calculate total budget
        const totalBudget = dailyAverage * forecastDays;
        
        // Update the UI elements
        const budgetPeriodText = document.getElementById('budget-period-text');
        const budgetCurrency = document.getElementById('budget-currency');
        const budgetInput = document.getElementById('budget-input');
        const dailyBudgetText = document.getElementById('daily-budget-text');
        const budgetWarning = document.getElementById('budget-warning');
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
            
            // Apply styling based on validity
            if (!isValidBudget) {
                budgetInput.classList.add('invalid-budget-input');
            } else {
                budgetInput.classList.remove('invalid-budget-input');
            }
        }
        if (dailyBudgetText) {
            dailyBudgetText.textContent = 
                `~${currency}${formatNumber(dailyAverage)} per day based on ${forecastDays}-day period`;
            
            // Apply styling based on validity
            if (!isValidBudget) {
                dailyBudgetText.classList.add('invalid-budget');
            } else {
                dailyBudgetText.classList.remove('invalid-budget');
            }
        }
        
        // Show/hide warning message
        if (budgetWarning) {
            if (!isValidBudget) {
                budgetWarning.style.display = 'block';
            } else {
                budgetWarning.style.display = 'none';
            }
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
            const currency = '£';  // Always use '£'
            
            if (dailyBudgetText) {
                dailyBudgetText.textContent = 
                    `~${currency}${formatNumber(dailyAverage)} per day based on ${forecastDays}-day period`;
                
                // Remove invalid class as user is now manually setting budget
                dailyBudgetText.classList.remove('invalid-budget');
            }
            
            // Hide warning when user manually edits budget
            const budgetWarning = document.getElementById('budget-warning');
            if (budgetWarning) {
                budgetWarning.style.display = 'none';
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