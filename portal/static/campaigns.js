// Campaign management JavaScript

// Global state
let currentCampaigns = [];
let isFormVisible = false;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCampaigns();
});

// Toggle new campaign form visibility
function toggleNewCampaignForm() {
    const form = document.getElementById('new-campaign-form');
    isFormVisible = !isFormVisible;
    
    if (isFormVisible) {
        form.style.display = 'block';
        document.getElementById('name').focus();
    } else {
        form.style.display = 'none';
        clearForm();
    }
}

// Clear form fields
function clearForm() {
    document.getElementById('campaign-form').reset();
}

// Submit new campaign
function submitCampaign(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const campaignData = {
        name: formData.get('name'),
        target_trade: formData.get('target_trade'),
        target_borough: formData.get('target_borough'),
        brand: formData.get('brand') || 'Default Brand',
        description: `Campaign targeting ${formData.get('target_trade')} in ${formData.get('target_borough')}`,
        status: 'active'
    };
    
    fetch('/api/campaigns', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(campaignData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error creating campaign: ' + data.error);
        } else {
            toggleNewCampaignForm();
            loadCampaigns(); // Refresh the table
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to create campaign');
    });
}

// Load campaigns from API
function loadCampaigns() {
    fetch('/api/campaigns')
        .then(response => response.json())
        .then(data => {
            currentCampaigns = data.campaigns || [];
            renderCampaignsTable();
        })
        .catch(error => {
            console.error('Error loading campaigns:', error);
        });
}

// Render campaigns table
function renderCampaignsTable() {
    const tbody = document.getElementById('campaigns-tbody');
    tbody.innerHTML = '';
    
    if (currentCampaigns.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--text-secondary);">No campaigns found. Create your first campaign to get started.</td></tr>';
        return;
    }
    
    currentCampaigns.forEach(campaign => {
        const row = document.createElement('tr');
        row.onclick = () => showStatsPanel(campaign);
        
        // Calculate metrics (mock data for now)
        const leadCount = Math.floor(Math.random() * 50) + 10;
        const enrichedCount = Math.floor(leadCount * 0.7);
        const proposalsSent = Math.floor(enrichedCount * 0.4);
        const replies = Math.floor(proposalsSent * 0.3);
        const interested = Math.floor(replies * 0.6);
        
        row.innerHTML = `
            <td><strong>${campaign.name}</strong></td>
            <td>${campaign.description || 'Standard outreach'}</td>
            <td><span style="background: var(--primary-color); color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">${campaign.target_trade}</span></td>
            <td>${campaign.target_borough}</td>
            <td>${leadCount}</td>
            <td>${enrichedCount}</td>
            <td>${proposalsSent}</td>
            <td>${replies}</td>
            <td><span style="color: var(--success-color); font-weight: 600;">${interested}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

// Show stats panel for selected campaign
function showStatsPanel(campaign) {
    const panel = document.getElementById('stats-panel');
    const title = document.getElementById('stats-title');
    
    title.textContent = `${campaign.name} Statistics`;
    
    // Calculate mock statistics
    const conversionRate = (Math.random() * 15 + 5).toFixed(1) + '%';
    const avgResponseTime = Math.floor(Math.random() * 48 + 12) + 'h';
    const costPerLead = '$' + (Math.random() * 50 + 25).toFixed(2);
    const roi = (Math.random() * 200 + 150).toFixed(0) + '%';
    const qualityScore = (Math.random() * 2 + 8).toFixed(1) + '/10';
    
    document.getElementById('conversion-rate').textContent = conversionRate;
    document.getElementById('avg-response-time').textContent = avgResponseTime;
    document.getElementById('cost-per-lead').textContent = costPerLead;
    document.getElementById('roi').textContent = roi;
    document.getElementById('quality-score').textContent = qualityScore;
    
    panel.style.display = 'block';
}

// Close stats panel
function closeStatsPanel() {
    document.getElementById('stats-panel').style.display = 'none';
}

// Close panel when clicking outside
document.addEventListener('click', function(event) {
    const panel = document.getElementById('stats-panel');
    const table = document.getElementById('campaigns-table');
    
    if (panel.style.display === 'block' && 
        !panel.contains(event.target) && 
        !table.contains(event.target)) {
        closeStatsPanel();
    }
});

// Updated form toggle to use CSS classes
function toggleNewCampaignForm() {
    const form = document.getElementById('new-campaign-form');
    if (form.classList.contains('hidden')) {
        form.classList.remove('hidden');
        const nameInput = document.getElementById('name');
        if (nameInput) nameInput.focus();
    } else {
        form.classList.add('hidden');
    }
}

// Show campaign stats function to match template
function showCampaignStats(campaignId, campaignName) {
    const panel = document.getElementById('campaign-stats');
    const title = document.getElementById('stats-title');
    
    title.textContent = `${campaignName} Statistics`;
    
    // Mock statistics
    document.getElementById('conversion-rate').textContent = (Math.random() * 15 + 5).toFixed(1) + '%';
    document.getElementById('response-rate').textContent = (Math.random() * 40 + 30).toFixed(1) + '%';
    document.getElementById('enrichment-rate').textContent = (Math.random() * 20 + 70).toFixed(1) + '%';
    document.getElementById('proposal-rate').textContent = (Math.random() * 20 + 40).toFixed(1) + '%';
    document.getElementById('cost-per-lead').textContent = '$' + (Math.random() * 30 + 20).toFixed(2);
    
    panel.classList.remove('hidden');
}

// Hide campaign stats
function hideCampaignStats() {
    document.getElementById('campaign-stats').classList.add('hidden');
}