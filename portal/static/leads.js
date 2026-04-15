/**
 * Leads Table Filtering JavaScript
 * Provides dynamic filtering for the leads table by trade and borough
 */

// Global variables
let allLeads = [];
let currentFilters = {
    trade: '',
    borough: ''
};

// DOM elements
const tradeFilter = document.getElementById('tradeFilter');
const boroughFilter = document.getElementById('boroughFilter');
const clearFiltersBtn = document.getElementById('clearFilters');
const leadsTable = document.getElementById('leadsTable');
const tableBody = leadsTable.querySelector('tbody');

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadLeadsData();
    setupEventListeners();
});

/**
 * Load leads data from API and populate table
 */
async function loadLeadsData() {
    try {
        const response = await fetch('/api/leads');
        if (!response.ok) {
            throw new Error('Failed to fetch leads data');
        }
        
        allLeads = await response.json();
        populateTradeFilter();
        renderTable(allLeads);
    } catch (error) {
        console.error('Error loading leads data:', error);
        showError('Failed to load leads data');
    }
}

/**
 * Populate trade filter dropdown with unique trades from data
 */
function populateTradeFilter() {
    const trades = [...new Set(allLeads.map(lead => lead.trade))].sort();
    
    // Clear existing options (except "All Trades")
    while (tradeFilter.children.length > 1) {
        tradeFilter.removeChild(tradeFilter.lastChild);
    }
    
    // Add trade options
    trades.forEach(trade => {
        const option = document.createElement('option');
        option.value = trade;
        option.textContent = trade;
        tradeFilter.appendChild(option);
    });
}

/**
 * Setup event listeners for filters
 */
function setupEventListeners() {
    tradeFilter.addEventListener('change', handleFilterChange);
    boroughFilter.addEventListener('change', handleFilterChange);
    clearFiltersBtn.addEventListener('click', clearFilters);
}

/**
 * Handle filter change events
 */
function handleFilterChange() {
    currentFilters.trade = tradeFilter.value;
    currentFilters.borough = boroughFilter.value;
    
    const filteredLeads = filterLeads(allLeads);
    renderTable(filteredLeads);
}

/**
 * Filter leads based on current filter selections
 */
function filterLeads(leads) {
    return leads.filter(lead => {
        const matchesTrade = !currentFilters.trade || lead.trade === currentFilters.trade;
        const matchesBorough = !currentFilters.borough || lead.borough === currentFilters.borough;
        
        return matchesTrade && matchesBorough;
    });
}

/**
 * Clear all filters and show all leads
 */
function clearFilters() {
    tradeFilter.value = '';
    boroughFilter.value = '';
    currentFilters.trade = '';
    currentFilters.borough = '';
    
    renderTable(allLeads);
}

/**
 * Render the leads table with given data
 */
function renderTable(leads) {
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (leads.length === 0) {
        showNoResults();
        return;
    }
    
    // Add rows for each lead
    leads.forEach(lead => {
        const row = createTableRow(lead);
        tableBody.appendChild(row);
    });
}

/**
 * Create a table row for a lead
 */
function createTableRow(lead) {
    const row = document.createElement('tr');
    row.setAttribute('data-trade', lead.trade);
    row.setAttribute('data-borough', lead.borough);
    
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };
    
    row.innerHTML = `
        <td>${escapeHtml(lead.name)}</td>
        <td>${escapeHtml(lead.trade)}</td>
        <td>${escapeHtml(lead.borough)}</td>
        <td><span class="score-badge score-${getScoreClass(lead.enrichment_score)}">${lead.enrichment_score}</span></td>
        <td>${formatDate(lead.date_created)}</td>
    `;
    
    return row;
}

/**
 * Get CSS class for enrichment score styling
 */
function getScoreClass(score) {
    if (score >= 80) return 'high';
    if (score >= 60) return 'medium';
    return 'low';
}

/**
 * Show no results message
 */
function showNoResults() {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td colspan="5" class="no-results">
            No leads match your current filters.
            <button onclick="clearFilters()" class="btn btn-link">Clear filters</button>
        </td>
    `;
    tableBody.appendChild(row);
}

/**
 * Show error message
 */
function showError(message) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td colspan="5" class="error-message">
            ${escapeHtml(message)}
            <button onclick="loadLeadsData()" class="btn btn-link">Retry</button>
        </td>
    `;
    tableBody.appendChild(row);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Get current filter status for debugging
 */
function getFilterStatus() {
    return {
        totalLeads: allLeads.length,
        filteredLeads: filterLeads(allLeads).length,
        currentFilters: { ...currentFilters }
    };
}
// Detail Panel Variables
let detailPanel;
let currentFilteredLeads = [];

// Initialize detail panel functionality
function initDetailPanel() {
    detailPanel = document.getElementById('leadDetailPanel');
    const closeBtn = document.getElementById('closeDetailPanel');
    const overlay = document.querySelector('.detail-panel-overlay');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDetailPanel);
    }
    
    if (overlay) {
        overlay.addEventListener('click', closeDetailPanel);
    }
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && detailPanel && detailPanel.style.display === 'block') {
            closeDetailPanel();
        }
    });
}

// Enhanced createTableRow function with click handler
function createTableRowWithDetail(lead, index) {
    const row = document.createElement('tr');
    row.setAttribute('data-trade', lead.trade);
    row.setAttribute('data-borough', lead.borough);
    row.style.cursor = 'pointer';
    
    // Add click handler for detail panel
    row.addEventListener('click', () => showLeadDetail(lead));
    
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };
    
    row.innerHTML = `
        <td>${escapeHtml(lead.name)}</td>
        <td>${escapeHtml(lead.trade)}</td>
        <td>${escapeHtml(lead.borough)}</td>
        <td><span class="score-badge score-${getScoreClass(lead.enrichment_score)}">${lead.enrichment_score}</span></td>
        <td>${formatDate(lead.date_created)}</td>
    `;
    
    return row;
}

// Show lead detail panel
function showLeadDetail(lead) {
    if (!detailPanel) {
        initDetailPanel();
    }
    
    populateLeadDetails(lead);
    detailPanel.style.display = 'block';
}

// Populate lead details
function populateLeadDetails(lead) {
    // Header
    setElementText('detailLeadName', lead.name || 'Unknown Lead');
    
    // Contact Information
    setElementText('detailName', lead.name || 'N/A');
    setElementText('detailEmail', lead.email || 'N/A');
    setElementText('detailPhone', lead.phone || 'N/A');
    setElementText('detailAddress', lead.address || 'N/A');
    
    // Project Information
    setElementText('detailTrade', lead.trade || 'N/A');
    setElementText('detailBorough', lead.borough || 'N/A');
    setElementText('detailProjectType', lead.project_type || 'General');
    setElementText('detailBudget', lead.budget || 'Not specified');
    
    // Enrichment Details
    setElementText('detailEnrichmentScore', (lead.enrichment_score || 0) + '%');
    
    // Mock enrichment breakdown
    const baseScore = lead.enrichment_score || 0;
    setElementText('detailContactScore', Math.min(100, baseScore + 10) + '%');
    setElementText('detailProjectScore', Math.min(100, baseScore + 5) + '%');
    setElementText('detailBudgetScore', Math.min(100, baseScore - 5) + '%');
    
    // Mock interaction history
    populateInteractionHistory();
}

// Helper function to safely set element text
function setElementText(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = text;
    }
}

// Populate mock interaction history
function populateInteractionHistory() {
    const historyContainer = document.getElementById('detailInteractionHistory');
    if (!historyContainer) return;
    
    const interactions = [
        { icon: '📧', title: 'Initial Contact Received', time: 'Today, 2:30 PM' },
        { icon: '🔍', title: 'Lead Enrichment Completed', time: 'Today, 2:35 PM' },
        { icon: '📞', title: 'Follow-up Call Scheduled', time: 'Tomorrow, 10:00 AM' }
    ];
    
    historyContainer.innerHTML = interactions.map(interaction => `
        <div class="timeline-item">
            <div class="timeline-icon">${interaction.icon}</div>
            <div class="timeline-content">
                <div class="timeline-title">${interaction.title}</div>
                <div class="timeline-time">${interaction.time}</div>
            </div>
        </div>
    `).join('');
}

// Close detail panel
function closeDetailPanel() {
    if (detailPanel) {
        detailPanel.style.display = 'none';
    }
}

// Update existing setupEventListeners function
function setupEventListenersEnhanced() {
    tradeFilter.addEventListener('change', handleFilterChange);
    boroughFilter.addEventListener('change', handleFilterChange);
    clearFiltersBtn.addEventListener('click', clearFilters);
    initDetailPanel();
}

// Update createTableRow to use enhanced version
const originalCreateTableRow = createTableRow;
function createTableRow(lead, index) {
    return createTableRowWithDetail(lead, index);
}

// Initialize enhanced functionality
document.addEventListener('DOMContentLoaded', function() {
    loadLeadsData();
    setupEventListenersEnhanced();
});