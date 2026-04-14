document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const selectAllCheckbox = document.getElementById('select-all');
    const leadCheckboxes = document.querySelectorAll('.lead-checkbox');
    const bulkOperationsBar = document.getElementById('bulk-operations');
    const selectedCountSpan = document.getElementById('selected-count');
    const expandButtons = document.querySelectorAll('.expand-btn');
    const tradeFilter = document.getElementById('trade-filter');
    const boroughFilter = document.getElementById('borough-filter');
    const scoreMinFilter = document.getElementById('score-min');
    const scoreMaxFilter = document.getElementById('score-max');
    const scoreRangeSpan = document.getElementById('score-range');
    const statusFilter = document.getElementById('status-filter');

    // Bulk selection
    function updateBulkOperations() {
        const checkedBoxes = document.querySelectorAll('.lead-checkbox:checked');
        const count = checkedBoxes.length;
        if (selectedCountSpan) selectedCountSpan.textContent = count;
        if (bulkOperationsBar) bulkOperationsBar.style.display = count > 0 ? 'flex' : 'none';
        
        if (selectAllCheckbox) {
            if (count === 0) {
                selectAllCheckbox.indeterminate = false;
                selectAllCheckbox.checked = false;
            } else if (count === leadCheckboxes.length) {
                selectAllCheckbox.indeterminate = false;
                selectAllCheckbox.checked = true;
            } else {
                selectAllCheckbox.indeterminate = true;
            }
        }
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            leadCheckboxes.forEach(cb => cb.checked = this.checked);
            updateBulkOperations();
        });
    }

    leadCheckboxes.forEach(cb => cb.addEventListener('change', updateBulkOperations));

    // Row expansion
    expandButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const leadId = this.getAttribute('data-lead-id');
            const detailsRow = document.getElementById(`details-${leadId}`);
            if (detailsRow) {
                const isHidden = detailsRow.style.display === 'none';
                detailsRow.style.display = isHidden ? 'table-row' : 'none';
                this.innerHTML = isHidden ? 
                    '<span class="expand-icon expanded">▼</span> Hide' :
                    '<span class="expand-icon">▼</span> Details';
            }
        });
    });

    // Filters
    function updateScoreRange() {
        if (scoreMinFilter && scoreMaxFilter && scoreRangeSpan) {
            scoreRangeSpan.textContent = `${scoreMinFilter.value} - ${scoreMaxFilter.value}`;
            applyFilters();
        }
    }

    function applyFilters() {
        const trade = tradeFilter ? tradeFilter.value.toLowerCase() : '';
        const borough = boroughFilter ? boroughFilter.value.toLowerCase() : '';
        const scoreMin = scoreMinFilter ? parseInt(scoreMinFilter.value) : 0;
        const scoreMax = scoreMaxFilter ? parseInt(scoreMaxFilter.value) : 100;
        const status = statusFilter ? statusFilter.value.toLowerCase() : '';

        document.querySelectorAll('.lead-row').forEach(row => {
            const rowTrade = row.children[3]?.textContent.toLowerCase() || '';
            const rowBorough = row.children[4]?.textContent.toLowerCase() || '';
            const scoreEl = row.children[5]?.querySelector('.score-badge');
            const rowScore = scoreEl ? parseInt(scoreEl.textContent) || 0 : 0;
            const rowStatus = row.children[6]?.textContent.toLowerCase() || '';
            
            const matches = (!trade || rowTrade.includes(trade)) &&
                          (!borough || rowBorough.includes(borough)) &&
                          (rowScore >= scoreMin && rowScore <= scoreMax) &&
                          (!status || rowStatus.includes(status));
            
            row.style.display = matches ? 'table-row' : 'none';
        });
    }

    if (scoreMinFilter) scoreMinFilter.addEventListener('input', updateScoreRange);
    if (scoreMaxFilter) scoreMaxFilter.addEventListener('input', updateScoreRange);
    if (tradeFilter) tradeFilter.addEventListener('change', applyFilters);
    if (boroughFilter) boroughFilter.addEventListener('change', applyFilters);
    if (statusFilter) statusFilter.addEventListener('change', applyFilters);

    // Bulk operations
    ['bulk-enrich', 'bulk-proposals', 'bulk-export', 'bulk-tag'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', function() {
                const selected = Array.from(document.querySelectorAll('.lead-checkbox:checked')).map(cb => cb.value);
                if (id === 'bulk-tag') {
                    const name = prompt('Campaign name:');
                    if (name) alert(`Tagged ${selected.length} leads with "${name}"`);
                } else {
                    alert(`${id.replace('bulk-', '')} for ${selected.length} leads`);
                }
            });
        }
    });

    updateScoreRange();
});