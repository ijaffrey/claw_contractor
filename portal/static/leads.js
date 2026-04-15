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
        const row = createTableRowWithDetail(lead);
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

// Detail Panel Functionality
function initDetailPanel() {
    const panel = document.getElementById('detailPanel');
    if (!panel) return;
    
    const overlay = panel.querySelector('.detail-panel-overlay');
    const closeBtn = panel.querySelector('.close-btn');
    
    if (overlay) overlay.addEventListener('click', closeDetailPanel);
    if (closeBtn) closeBtn.addEventListener('click', closeDetailPanel);
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && panel.style.display === 'block') {
            closeDetailPanel();
        }
    });
}

// Open detail panel
function openDetailPanel(lead) {
    const panel = document.getElementById('detailPanel');
    if (!panel) return;
    
    populateDetailPanel(lead);
    panel.style.display = 'block';
}

// Close detail panel
function closeDetailPanel() {
    const panel = document.getElementById('detailPanel');
    if (panel) panel.style.display = 'none';
}

// Populate detail panel with lead data
function populateDetailPanel(lead) {
    // Contact Information
    setElement('detailName', lead.name);
    setElement('detailEmail', lead.email);
    setElement('detailPhone', lead.phone);
    setElement('detailAddress', lead.address);
    
    // Project Details
    setElement('detailTrade', lead.trade);
    setElement('detailBorough', lead.borough);
    setElement('detailProjectType', lead.project_type || 'General');
    setElement('detailBudget', lead.budget_range || '$5,000 - $25,000');
    
    // Enrichment Details
    setElement('detailEnrichmentScore', lead.enrichment_score);
    setElement('detailLeadSource', 'Permit Database');
    setElement('detailQualityRating', getQualityRating(lead.enrichment_score));
    setElement('detailVerificationStatus', getVerificationStatus(lead.enrichment_score));
    
    // Timeline
    setElement('detailDateCreated', formatDate(lead.date_created));
    setElement('detailLastContact', 'Never');
    setElement('detailFollowupDate', 'Not Set');
    setElement('detailStatus', 'New');
    
    // Generate interaction history
    populateInteractionHistory(lead);
}

// Helper function to set element text
function setElement(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value || '-';
}

// Get quality rating based on score
function getQualityRating(score) {
    if (!score) return 'Unknown';
    if (score >= 80) return 'High Quality';
    if (score >= 60) return 'Medium Quality';
    return 'Low Quality';
}

// Get verification status based on score
function getVerificationStatus(score) {
    if (!score) return 'Unverified';
    if (score >= 70) return 'Verified';
    if (score >= 50) return 'Partially Verified';
    return 'Unverified';
}

// Populate interaction history
function populateInteractionHistory(lead) {
    const container = document.getElementById('interactionHistory');
    if (!container) return;
    
    const interactions = generateMockInteractions(lead);
    container.innerHTML = '';
    
    if (interactions.length === 0) {
        container.innerHTML = '<p class="no-interactions">No interactions yet</p>';
        return;
    }
    
    interactions.forEach(interaction => {
        const item = document.createElement('div');
        item.className = 'interaction-item';
        item.innerHTML = `
            <div class="interaction-date">${formatDate(interaction.date)}</div>
            <div class="interaction-type">${interaction.type}</div>
            <div class="interaction-details">${interaction.details}</div>
        `;
        container.appendChild(item);
    });
}

// Generate mock interactions based on lead
function generateMockInteractions(lead) {
    const interactions = [];
    const score = lead.enrichment_score || 0;
    const baseDate = new Date(lead.date_created || Date.now());
    
    interactions.push({
        date: baseDate.toISOString(),
        type: 'Lead Created',
        details: 'Lead generated from permit database'
    });
    
    if (score > 50) {
        const emailDate = new Date(baseDate.getTime() + 24 * 60 * 60 * 1000);
        interactions.push({
            date: emailDate.toISOString(),
            type: 'Email Sent',
            details: 'Initial contact email sent'
        });
    }
    
    if (score > 70) {
        const followDate = new Date(baseDate.getTime() + 3 * 24 * 60 * 60 * 1000);
        interactions.push({
            date: followDate.toISOString(),
            type: 'Follow-up',
            details: 'Follow-up email with project details'
        });
    }
    
    return interactions.sort((a, b) => new Date(b.date) - new Date(a.date));
}

// Initialize detail panel on load
document.addEventListener('DOMContentLoaded', function() {
    initDetailPanel();
});

// Create table row with detail panel click handler
function createTableRowWithDetail(lead) {
    const row = document.createElement('tr');
    row.style.cursor = 'pointer';
    row.className = 'clickable-row';
    
    // Add click handler for detail panel
    row.addEventListener('click', () => openDetailPanel(lead));
    
    const formatDate = (dateString) => {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };
    
    row.innerHTML = `
        <td>${escapeHtml(lead.name || 'Unknown')}</td>
        <td>${escapeHtml(lead.trade || 'Unknown')}</td>
        <td>${escapeHtml(lead.borough || 'Unknown')}</td>
        <td><span class="score-badge">${lead.enrichment_score || 0}</span></td>
        <td>${formatDate(lead.date_created)}</td>
    `;
    
    return row;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}