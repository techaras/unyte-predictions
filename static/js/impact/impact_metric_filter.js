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
    
    // Get all metric rows
    const metricRows = document.querySelectorAll('.forecast-row');
    
    // For each row, check if its metric is in selected metrics
    let visibleRows = 0;
    metricRows.forEach(row => {
        const metricName = row.getAttribute('data-metric-name');
        
        if (selectedMetrics.includes(metricName)) {
            row.style.display = ''; // Show the row
            visibleRows++;
        } else {
            row.style.display = 'none'; // Hide the row
        }
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
    noMetricsMsg.style.display = visibleRows > 0 ? 'none' : 'table-row';
    
    // Update button to show count of selected metrics
    updateMetricCount(selectedMetrics.length);
}

function updateMetricCount(count) {
    const dropdownBtn = document.getElementById('metric-dropdown-btn');
    
    // Update the text to show count
    dropdownBtn.querySelector('span').textContent = `Metrics (${count})`;
}