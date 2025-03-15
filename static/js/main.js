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
});