document.addEventListener('DOMContentLoaded', function() {
    const budgetSlider = document.getElementById('budget-slider');
    const currentBudget = document.getElementById('current-budget');
    const elasticityCards = document.querySelectorAll('.elasticity-card');
    
    if (budgetSlider && currentBudget) {
        // Initialize with current budget
        const originalBudget = parseFloat(budgetSlider.getAttribute('data-original-budget'));
        let currentBudgetValue = originalBudget;
        
        // Update budget display
        function updateBudgetDisplay() {
            const currency = currentBudget.getAttribute('data-currency') || '£';
            currentBudget.textContent = `${currency}${formatNumber(currentBudgetValue)}`;
            
            // Calculate percent change from original
            const percentChange = ((currentBudgetValue - originalBudget) / originalBudget) * 100;
            
            // Update all elasticity cards
            elasticityCards.forEach(card => {
                const metric = card.getAttribute('data-metric');
                const coefficient = parseFloat(card.getAttribute('data-coefficient'));
                const baselineValue = parseFloat(card.getAttribute('data-baseline'));
                
                // Calculate new expected value based on budget change
                // This is a simplified calculation - actual elasticity might be more complex
                const newValue = baselineValue * (1 + (coefficient * percentChange / 100));
                
                // Update card with new value
                const valueElement = card.querySelector('.predicted-value');
                if (valueElement) {
                    valueElement.textContent = formatNumber(newValue);
                    
                    // Color code based on direction
                    if (newValue > baselineValue) {
                        valueElement.classList.add('positive-impact');
                        valueElement.classList.remove('negative-impact');
                    } else if (newValue < baselineValue) {
                        valueElement.classList.add('negative-impact');
                        valueElement.classList.remove('positive-impact');
                    } else {
                        valueElement.classList.remove('positive-impact');
                        valueElement.classList.remove('negative-impact');
                    }
                }
                
                // Update percent change
                const percentElement = card.querySelector('.percent-change');
                if (percentElement) {
                    const metricChange = ((newValue - baselineValue) / baselineValue) * 100;
                    percentElement.textContent = `${metricChange.toFixed(1)}%`;
                }
            });
        }
        
        // Format numbers with commas
        function formatNumber(num) {
            return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
        
        // Update when slider changes
        budgetSlider.addEventListener('input', function() {
            // Get percent value (0-200%)
            const percent = parseInt(this.value);
            currentBudgetValue = originalBudget * (percent / 100);
            updateBudgetDisplay();
        });
        
        // Initialize display
        updateBudgetDisplay();
    }
});