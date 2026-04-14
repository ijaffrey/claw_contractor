document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const leadCheckboxes = document.querySelectorAll('.lead-select');
    const bulkOpsBar = document.getElementById('bulk-ops-bar');
    const selectedCountSpan = document.querySelector('.selected-count');
    const expandToggles = document.querySelectorAll('.expand-toggle');
    const scoreRangeInput = document.getElementById('score-range');
    const scoreDisplay = document.getElementById('score-display');

    // Initialize score range display
    updateScoreDisplay();

    // Select All functionality
    selectAllCheckbox.addEventListener('change', function() {
        leadCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateBulkOperations();
    });

    // Individual checkbox handling
    leadCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectAll();
            updateBulkOperations();
        });
    });

    // Expand/collapse details
    expandToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const detailsRow = document.getElementById(targetId);
            
            if (detailsRow.style.display === 'none') {
                detailsRow.style.display = 'table-row';
                this.classList.add('expanded');
            } else {
                detailsRow.style.display = 'none';
                this.classList.remove('expanded');
            }
        });
    });

    // Filter functionality
    const filterInputs = document.querySelectorAll('#trade-filter, #borough-filter, #outreach-filter');
    filterInputs.forEach(filter => {
        filter.addEventListener('change', applyFilters);
    });

    scoreRangeInput.addEventListener('input', function() {
        updateScoreDisplay();
        applyFilters();
    });

    // Bulk operation buttons
    document.getElementById('bulk-enrich')?.addEventListener('click', function() {
        const selected = getSelectedLeadIds();
        alert(`Enriching ${selected.length} leads...`);
    });

    document.getElementById('bulk-proposals')?.addEventListener('click', function() {
        const selected = getSelectedLeadIds();
        alert(`Generating proposals for ${selected.length} leads...`);
    });

    document.getElementById('bulk-export')?.addEventListener('click', function() {
        const selected = getSelectedLeadIds();
        alert(`Exporting ${selected.length} leads to CSV...`);
    });

    document.getElementById('bulk-tag')?.addEventListener('click', function() {
        const selected = getSelectedLeadIds();
        const campaign = prompt('Enter campaign name:');
        if (campaign) {
            alert(`Tagging ${selected.length} leads with campaign: ${campaign}`);
        }
    });

    function updateSelectAll() {
        const checkedCount = Array.from(leadCheckboxes).filter(cb => cb.checked).length;
        selectAllCheckbox.checked = checkedCount === leadCheckboxes.length;
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < leadCheckboxes.length;
    }

    function updateBulkOperations() {
        const selectedCount = Array.from(leadCheckboxes).filter(cb => cb.checked).length;
        
        if (selectedCount > 0) {
            bulkOpsBar.style.display = 'flex';
            selectedCountSpan.textContent = `${selectedCount} selected`;
        } else {
            bulkOpsBar.style.display = 'none';
        }
    }

    function getSelectedLeadIds() {
        return Array.from(leadCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    }

    function updateScoreDisplay() {
        scoreDisplay.textContent = scoreRangeInput.value + '+';
    }

    function applyFilters() {
        const tradeFilter = document.getElementById('trade-filter').value;
        const boroughFilter = document.getElementById('borough-filter').value;
        const scoreFilter = parseInt(scoreRangeInput.value);
        const outreachFilter = document.getElementById('outreach-filter').value;

        const rows = document.querySelectorAll('.lead-row');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const trade = cells[2].textContent.trim();
            const borough = cells[3].textContent.trim();
            const score = parseInt(cells[4].querySelector('.score-badge').textContent.trim());
            const outreach = cells[5].textContent.trim();
            
            const tradeMatch = !tradeFilter || trade === tradeFilter;
            const boroughMatch = !boroughFilter || borough === boroughFilter;
            const scoreMatch = score >= scoreFilter;
            const outreachMatch = !outreachFilter || outreach === outreachFilter;
            
            const isVisible = tradeMatch && boroughMatch && scoreMatch && outreachMatch;
            row.style.display = isVisible ? 'table-row' : 'none';
        });
        
        updateBulkOperations();
    }
});