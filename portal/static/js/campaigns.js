// Campaigns JavaScript for Lead Management

// Bulk selection functionality
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const leadCheckboxes = document.querySelectorAll('.lead-checkbox');
    
    leadCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBulkOperations();
}

function updateBulkOperations() {
    const checkedBoxes = document.querySelectorAll('.lead-checkbox:checked');
    const bulkOperations = document.querySelector('.bulk-operations');
    const selectedCount = document.getElementById('selected-count');
    
    if (checkedBoxes.length > 0) {
        bulkOperations.style.display = 'flex';
        if (selectedCount) {
            selectedCount.textContent = checkedBoxes.length;
        }
    } else {
        bulkOperations.style.display = 'none';
    }
}

// Row expansion functionality
function toggleRowExpansion(leadId) {
    const detailsRow = document.getElementById(`details-${leadId}`);
    const expandButton = document.querySelector(`[onclick="toggleRowExpansion(${leadId})"]`);
    
    if (detailsRow.style.display === 'none' || !detailsRow.style.display) {
        detailsRow.style.display = 'table-row';
        expandButton.innerHTML = '↑';
    } else {
        detailsRow.style.display = 'none';
        expandButton.innerHTML = '↓';
    }
}

// Bulk operations handlers
function bulkEnrich() {
    const selectedLeads = getSelectedLeads();
    if (selectedLeads.length === 0) return;
    
    if (confirm(`Enrich ${selectedLeads.length} selected leads?`)) {
        console.log('Bulk enriching leads:', selectedLeads);
        alert('Enrichment started for selected leads');
    }
}

function bulkGenerateProposals() {
    const selectedLeads = getSelectedLeads();
    if (selectedLeads.length === 0) return;
    
    if (confirm(`Generate proposals for ${selectedLeads.length} selected leads?`)) {
        console.log('Generating proposals for leads:', selectedLeads);
        alert('Proposal generation started for selected leads');
    }
}

function bulkExportCSV() {
    const selectedLeads = getSelectedLeads();
    if (selectedLeads.length === 0) return;
    
    console.log('Exporting leads to CSV:', selectedLeads);
    alert('CSV export started for selected leads');
}

function bulkTagCampaign() {
    const selectedLeads = getSelectedLeads();
    if (selectedLeads.length === 0) return;
    
    const campaignTag = prompt('Enter campaign tag:');
    if (campaignTag) {
        console.log('Tagging leads with campaign:', campaignTag, selectedLeads);
        alert(`Tagged ${selectedLeads.length} leads with campaign: ${campaignTag}`);
    }
}

// Utility function to get selected lead IDs
function getSelectedLeads() {
    const checkedBoxes = document.querySelectorAll('.lead-checkbox:checked');
    return Array.from(checkedBoxes).map(checkbox => {
        return checkbox.closest('.lead-row').dataset.leadId;
    });
}

// Filter functionality
function applyFilters() {
    const tradeFilter = document.getElementById('trade-filter')?.value;
    const boroughFilter = document.getElementById('borough-filter')?.value;
    const scoreFilter = document.getElementById('score-filter')?.value;
    const statusFilter = document.getElementById('status-filter')?.value;
    
    const rows = document.querySelectorAll('.lead-row');
    
    rows.forEach(row => {
        let shouldShow = true;
        
        // Apply trade filter
        if (tradeFilter && tradeFilter !== 'all') {
            const tradeCell = row.children[3]?.textContent;
            if (tradeCell && !tradeCell.toLowerCase().includes(tradeFilter.toLowerCase())) {
                shouldShow = false;
            }
        }
        
        // Apply score filter
        if (scoreFilter && scoreFilter !== 'all') {
            const scoreBadge = row.querySelector('.score-badge');
            if (scoreBadge) {
                const score = parseInt(scoreBadge.textContent);
                switch(scoreFilter) {
                    case 'high':
                        if (score < 75) shouldShow = false;
                        break;
                    case 'medium':
                        if (score < 25 || score >= 75) shouldShow = false;
                        break;
                    case 'low':
                        if (score >= 25) shouldShow = false;
                        break;
                }
            }
        }
        
        row.style.display = shouldShow ? '' : 'none';
        const leadId = row.dataset.leadId;
        const detailsRow = document.getElementById(`details-${leadId}`);
        if (detailsRow) {
            detailsRow.style.display = shouldShow && detailsRow.style.display === 'table-row' ? 'table-row' : 'none';
        }
    });
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    const bulkOperations = document.querySelector('.bulk-operations');
    if (bulkOperations) {
        bulkOperations.style.display = 'none';
    }
    
    const filterSelects = document.querySelectorAll('.filter-group select');
    filterSelects.forEach(select => {
        select.addEventListener('change', applyFilters);
    });
    
    console.log('Campaigns page initialized');
});