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