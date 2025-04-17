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

// This is the simplest and most reliable solution to fix the metric filtering

function applyMetricFilters() {
    const checkboxList = document.getElementById('metric-checkbox-list');
    const checkboxes = checkboxList.querySelectorAll('input[type="checkbox"]');
    
    // Get array of selected metric names
    const selectedMetrics = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    
    // Get the table body
    const tableBody = document.getElementById('impact-table-body');
    
    // If we have no metrics selected, show message and return
    if (selectedMetrics.length === 0) {
        tableBody.innerHTML = '<tr class="no-metrics-message"><td colspan="8">No metrics selected. Please select at least one metric from the dropdown.</td></tr>';
        updateMetricCount(0);
        return;
    }
    
    // 1. Clear the table
    tableBody.innerHTML = '';
    
    // 2. Rebuild the table by rendering only the selected metrics
    impactData.forecasts.forEach(forecast => {
        // Filter metrics to only include selected ones
        const filteredMetrics = forecast.metrics.filter(metric => 
            selectedMetrics.includes(metric.name)
        );
        
        // Skip forecasts with no visible metrics
        if (filteredMetrics.length === 0) return;
        
        // Render each metric row
        filteredMetrics.forEach((metric, index) => {
            const row = document.createElement('tr');
            row.className = 'forecast-row';
            row.setAttribute('data-forecast-id', forecast.id);
            row.setAttribute('data-metric-name', metric.name);
            
            // Build the row HTML
            let rowHtml = '';
            
            // Only add title/platform/campaign cells for the first visible metric
            if (index === 0) {
                rowHtml += `
                    <td rowspan="${filteredMetrics.length}" class="forecast-cell">${forecast.title}</td>
                    <td rowspan="${filteredMetrics.length}" class="platform-cell">${forecast.platform}</td>
                    <td rowspan="${filteredMetrics.length}">${forecast.campaign}</td>
                `;
            }
            
            // Format value based on metric name
            let currentValue, simulatedValue;
            
            if (metric.name === 'ROAS') {
                currentValue = parseFloat(metric.current).toFixed(1);
                simulatedValue = parseFloat(metric.simulated).toFixed(1);
            } else if (metric.name === 'CTR' || metric.name === 'Conversion Rate') {
                currentValue = parseFloat(metric.current).toFixed(2);
                simulatedValue = parseFloat(metric.simulated).toFixed(2);
            } else {
                currentValue = parseInt(metric.current);
                simulatedValue = parseInt(metric.simulated);
            }
            
            // Determine impact class
            let impactClass = 'impact-neutral';
            if (metric.impact > 0) {
                impactClass = 'impact-positive';
            } else if (metric.impact < 0) {
                impactClass = 'impact-negative';
            }
            
            // Add the metric-specific cells
            rowHtml += `
                <td data-metric="${metric.name}">${metric.name}</td>
                <td class="metric-current" data-value="${metric.current}">${currentValue}</td>
                <td class="metric-simulated" data-metric="${metric.name}">${simulatedValue}</td>
                <td class="impact-value ${impactClass}" data-metric="${metric.name}">${parseFloat(metric.impact).toFixed(1)}%</td>
            `;
            
            // Add budget cell only for the first metric in each forecast
            if (index === 0) {
                rowHtml += `
                    <td rowspan="${filteredMetrics.length}" class="budget-cell">
                        ${forecast.budget && forecast.budget.value ? 
                          `${forecast.budget.currency}${parseInt(forecast.budget.value)}` : 
                          '--'}
                    </td>
                `;
            }
            
            // Set the row HTML
            row.innerHTML = rowHtml;
            
            // Add to table body
            tableBody.appendChild(row);
        });
    });
    
    // Update metric count
    updateMetricCount(selectedMetrics.length);
}

function updateMetricCount(count) {
    const dropdownBtn = document.getElementById('metric-dropdown-btn');
    
    // Update the text to show count
    dropdownBtn.querySelector('span').textContent = `Metrics (${count})`;
}