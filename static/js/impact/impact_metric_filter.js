// Metric selection and filtering functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize metric filter after impact data is loaded
    setupMetricFilter();
});

function setupMetricFilter() {
    // Get the dropdown button and content
    const dropdownBtn = document.getElementById('metric-dropdown-btn');
    const dropdown = document.getElementById('metric-dropdown');
    const checkboxList = document.getElementById('metric-checkbox-list');
    const selectAllBtn = document.getElementById('select-all-metrics');
    const applyBtn = document.getElementById('apply-metric-selection');

    // Toggle dropdown when button is clicked
    dropdownBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('show');
        
        // If dropdown is opening and empty, populate metrics
        if (dropdown.classList.contains('show') && checkboxList.children.length === 0) {
            populateMetricCheckboxes();
        }
    });

    // Close dropdown when clicking outside
    window.addEventListener('click', function(e) {
        if (dropdown.classList.contains('show') && !dropdown.contains(e.target) && e.target !== dropdownBtn) {
            dropdown.classList.remove('show');
        }
    });

    // Select all metrics
    selectAllBtn.addEventListener('click', function() {
        const checkboxes = checkboxList.querySelectorAll('input[type="checkbox"]');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
        });
        
        // Update button text
        selectAllBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
    });

    // Apply selected metrics
    applyBtn.addEventListener('click', function() {
        applyMetricFilters();
        dropdown.classList.remove('show');
    });
}

function populateMetricCheckboxes() {
    const checkboxList = document.getElementById('metric-checkbox-list');
    const forecasts = impactData.forecasts;
    
    // Get unique metrics from all forecasts
    const uniqueMetrics = new Set();
    forecasts.forEach(forecast => {
        forecast.metrics.forEach(metric => {
            uniqueMetrics.add(metric.name);
        });
    });
    
    // Convert to array
    const metricsList = Array.from(uniqueMetrics);
    
    // Sort metrics into categories and alphabetically within categories
    const metricCategories = {
        'Performance': ['Clicks', 'Impressions', 'CTR', 'Reach', 'Frequency'],
        'Conversion': ['Conversions', 'Conversion Rate', 'Conversion Value', 'ROAS', 'ROI'],
        'Cost': ['Cost', 'CPC', 'CPM', 'CPA', 'CPL']
    };
    
    // Create a mapping of metrics to categories
    const metricToCategoryMap = {};
    for (const category in metricCategories) {
        metricCategories[category].forEach(metric => {
            metricToCategoryMap[metric] = category;
        });
    }
    
    // Sort metrics: first by category, then alphabetically
    metricsList.sort((a, b) => {
        const categoryA = metricToCategoryMap[a] || 'Other';
        const categoryB = metricToCategoryMap[b] || 'Other';
        
        if (categoryA !== categoryB) {
            // If categories are different, sort by category priority
            const categoryOrder = ['Performance', 'Conversion', 'Cost', 'Other'];
            return categoryOrder.indexOf(categoryA) - categoryOrder.indexOf(categoryB);
        }
        
        // If categories are the same, sort alphabetically
        return a.localeCompare(b);
    });
    
    // Get default metrics to select
    const defaultMetrics = ['Clicks', 'Conversions', 'ROAS'];
    const availableDefaults = defaultMetrics.filter(m => metricsList.includes(m));
    
    // If none of the defaults are available, select the first metric
    const initialSelectedMetrics = availableDefaults.length > 0 ? 
        availableDefaults : 
        (metricsList.length > 0 ? [metricsList[0]] : []);
    
    // Clear existing content
    checkboxList.innerHTML = '';
    
    // Create the checkboxes
    metricsList.forEach(metricName => {
        const item = document.createElement('div');
        item.className = 'metric-checkbox-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `metric-${metricName.replace(/\s+/g, '-').toLowerCase()}`;
        checkbox.value = metricName;
        
        // Check if this metric should be selected by default
        checkbox.checked = initialSelectedMetrics.includes(metricName);
        
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = metricName;
        
        item.appendChild(checkbox);
        item.appendChild(label);
        checkboxList.appendChild(item);
    });
    
    // Apply initial filters
    applyMetricFilters();
}

function applyMetricFilters() {
    const checkboxList = document.getElementById('metric-checkbox-list');
    const checkboxes = checkboxList.querySelectorAll('input[type="checkbox"]');
    
    // Get array of selected metric names
    const selectedMetrics = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    
    // Get all metric rows
    const metricRows = document.querySelectorAll('.forecast-row');
    
    if (selectedMetrics.length === 0) {
        // If no metrics selected, select the first checkbox
        if (checkboxes.length > 0) {
            checkboxes[0].checked = true;
            selectedMetrics.push(checkboxes[0].value);
        } else {
            // If there are no checkboxes, show all rows (failsafe)
            metricRows.forEach(row => row.classList.remove('hidden-metric'));
            return;
        }
    }
    
    // For each row, check if its metric is in selected metrics
    metricRows.forEach(row => {
        const metricName = row.getAttribute('data-metric-name');
        
        if (selectedMetrics.includes(metricName)) {
            row.classList.remove('hidden-metric');
        } else {
            row.classList.add('hidden-metric');
        }
    });
    
    // Update rowspans for visible metrics
    updateRowspans(selectedMetrics);
    
    // Update the metrics counter in the dropdown button
    updateMetricsCounter(selectedMetrics);
}

function updateRowspans(selectedMetrics) {
    // For each forecast, count visible metrics and update rowspans
    const forecasts = impactData.forecasts;
    
    forecasts.forEach(forecast => {
        // Count visible metrics for this forecast
        const visibleMetricsCount = forecast.metrics.filter(metric => 
            selectedMetrics.includes(metric.name)
        ).length;
        
        if (visibleMetricsCount === 0) {
            // If no metrics visible, hide all rows for this forecast
            const forecastRows = document.querySelectorAll(`.forecast-row[data-forecast-id="${forecast.id}"]`);
            forecastRows.forEach(row => row.classList.add('hidden-metric'));
            return;
        }
        
        // Find the first visible row for this forecast
        const forecastRows = document.querySelectorAll(`.forecast-row[data-forecast-id="${forecast.id}"]`);
        const firstVisibleRowIndex = Array.from(forecastRows).findIndex(row => 
            selectedMetrics.includes(row.getAttribute('data-metric-name'))
        );
        
        if (firstVisibleRowIndex === -1) return;
        
        const firstVisibleRow = forecastRows[firstVisibleRowIndex];
        
        // Make all previously invisible rows visible but with no content
        for (let i = 0; i < firstVisibleRowIndex; i++) {
            forecastRows[i].classList.add('hidden-metric');
        }
        
        // Update rowspans for cells that span multiple rows
        const titleCell = firstVisibleRow.querySelector('.forecast-cell') || 
                          firstVisibleRow.querySelector('td:nth-child(1)');
                          
        const platformCell = firstVisibleRow.querySelector('.platform-cell') || 
                             firstVisibleRow.querySelector('td:nth-child(2)');
                             
        const campaignCell = firstVisibleRow.querySelector('td:nth-child(3)');
        const budgetCell = firstVisibleRow.querySelector('.budget-cell') || 
                           firstVisibleRow.querySelector('td:nth-child(8)');
        
        if (titleCell) titleCell.rowSpan = visibleMetricsCount;
        if (platformCell) platformCell.rowSpan = visibleMetricsCount;
        if (campaignCell) campaignCell.rowSpan = visibleMetricsCount;
        if (budgetCell) budgetCell.rowSpan = visibleMetricsCount;
    });
}

function updateMetricsCounter(selectedMetrics) {
    const dropdownBtn = document.getElementById('metric-dropdown-btn');
    const icon = dropdownBtn.querySelector('.metric-dropdown-icon');
    
    // Create or update the counter
    let counter = dropdownBtn.querySelector('.metrics-counter');
    if (!counter) {
        counter = document.createElement('span');
        counter.className = 'metrics-counter';
        dropdownBtn.insertBefore(counter, icon);
    }
    
    counter.textContent = `${selectedMetrics.length}`;
}