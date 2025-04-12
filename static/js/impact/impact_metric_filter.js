// static/js/impact/impact_metric_filter.js

// Metric dropdown functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get the dropdown button and content
    const dropdownBtn = document.getElementById('metric-dropdown-btn');
    const dropdown = document.getElementById('metric-dropdown');
    const checkboxList = document.getElementById('metric-checkbox-list');
    const selectAllBtn = document.getElementById('select-all-metrics');
    const applyBtn = document.getElementById('apply-metric-selection');

    // Ensure elements exist before adding event listeners
    if (!dropdownBtn || !dropdown) {
        console.error('Metric dropdown elements not found');
        return;
    }

    // Toggle dropdown when button is clicked
    dropdownBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Toggle the 'show' class
        dropdown.classList.toggle('show');
        
        // Optional: Log for debugging
        console.log('Dropdown toggled. Is showing:', dropdown.classList.contains('show'));
        
        // If dropdown is opening and empty, populate metrics
        if (dropdown.classList.contains('show') && checkboxList.children.length === 0) {
            populateMetricCheckboxes();
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (dropdown.classList.contains('show') && !dropdown.contains(e.target) && e.target !== dropdownBtn) {
            dropdown.classList.remove('show');
        }
    });
    
    // Select all metrics
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            const checkboxes = checkboxList.querySelectorAll('input[type="checkbox"]');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = !allChecked;
            });
            
            // Update button text
            selectAllBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
        });
    }

    // Apply selected metrics
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            applyMetricFilters();
            dropdown.classList.remove('show');
        });
    }
});

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
    
    // Default to all metrics checked
    const initialSelectedMetrics = metricsList;
    
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
        checkbox.checked = true; // Start with all checked
        
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = metricName;
        
        item.appendChild(checkbox);
        item.appendChild(label);
        checkboxList.appendChild(item);
    });
}

function applyMetricFilters() {
    const checkboxList = document.getElementById('metric-checkbox-list');
    const checkboxes = checkboxList.querySelectorAll('input[type="checkbox"]');
    
    // Get array of selected metric names
    const selectedMetrics = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    
    // First, show all rows to reset the table state
    document.querySelectorAll('.forecast-row').forEach(row => {
        row.style.display = '';
    });
    
    // Group rows by forecast ID
    const forecastGroups = {};
    document.querySelectorAll('.forecast-row').forEach(row => {
        const forecastId = row.getAttribute('data-forecast-id');
        if (!forecastGroups[forecastId]) {
            forecastGroups[forecastId] = [];
        }
        forecastGroups[forecastId].push(row);
    });
    
    // Process each forecast group
    let totalVisibleRows = 0;
    
    Object.keys(forecastGroups).forEach(forecastId => {
        const forecastRows = forecastGroups[forecastId];
        const firstRow = forecastRows[0]; // First row contains the title/platform/campaign cells
        
        // Count how many rows will be visible for this forecast
        const visibleRows = forecastRows.filter(row => {
            const metricName = row.getAttribute('data-metric-name');
            return selectedMetrics.includes(metricName);
        });
        
        // If no metrics visible for this forecast, hide all rows
        if (visibleRows.length === 0) {
            forecastRows.forEach(row => {
                row.style.display = 'none';
            });
            return; // Skip to next forecast
        }
        
        // Update rowspan attributes for visible rows
        const titleCell = firstRow.querySelector('td.forecast-cell');
        const platformCell = firstRow.querySelector('td.platform-cell');
        const campaignCell = firstRow.querySelector('td:nth-child(3)'); // 3rd cell is campaign
        
        if (titleCell) titleCell.setAttribute('rowspan', visibleRows.length);
        if (platformCell) platformCell.setAttribute('rowspan', visibleRows.length);
        if (campaignCell) campaignCell.setAttribute('rowspan', visibleRows.length);
        
        // Hide rows with non-selected metrics
        forecastRows.forEach(row => {
            const metricName = row.getAttribute('data-metric-name');
            if (!selectedMetrics.includes(metricName)) {
                row.style.display = 'none';
            } else {
                totalVisibleRows++;
            }
        });
    });
    
    // Check if we need to show "no metrics" message
    let noMetricsMsg = document.querySelector('.no-metrics-message');
    if (!noMetricsMsg) {
        // Create if it doesn't exist
        noMetricsMsg = document.createElement('tr');
        noMetricsMsg.className = 'no-metrics-message';
        noMetricsMsg.innerHTML = '<td colspan="8">No metrics selected. Please select at least one metric from the dropdown.</td>';
        document.querySelector('.simulator-table tbody').appendChild(noMetricsMsg);
    }
    
    // Show/hide message based on visible rows
    noMetricsMsg.style.display = totalVisibleRows > 0 ? 'none' : 'table-row';
    
    // Update button to show count of selected metrics
    updateMetricCount(selectedMetrics.length);
}

function updateMetricCount(count) {
    const dropdownBtn = document.getElementById('metric-dropdown-btn');
    
    // Update the text to show count
    dropdownBtn.querySelector('span').textContent = `Metrics (${count})`;
}