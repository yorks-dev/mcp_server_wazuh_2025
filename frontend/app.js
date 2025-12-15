// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentPipeline = 'simple';
let lastQueryResult = null;

// DOM Elements
const pipelineBtns = document.querySelectorAll('.pipeline-btn');
const nlQueryContainer = document.getElementById('nlQueryContainer');
const dslQueryContainer = document.getElementById('dslQueryContainer');
const queryInput = document.getElementById('queryInput');
const dslInput = document.getElementById('dslInput');
const executeBtn = document.getElementById('executeBtn');
const clearBtn = document.getElementById('clearBtn');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const successState = document.getElementById('successState');
const errorMessage = document.getElementById('errorMessage');
const nlResponse = document.getElementById('nlResponse');
const nlResponseText = document.getElementById('nlResponseText');
const formattedData = document.getElementById('formattedData');
const rawData = document.getElementById('rawData');
const dslData = document.getElementById('dslData');
const resultCount = document.getElementById('resultCount');
const executionTime = document.getElementById('executionTime');
const serverStatus = document.getElementById('serverStatus');
const serverStatusText = document.getElementById('serverStatusText');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');
const exampleChips = document.querySelectorAll('.example-chip');
const loadDslTemplate = document.getElementById('loadDslTemplate');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkServerStatus();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Pipeline selection
    pipelineBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const pipeline = btn.dataset.pipeline;
            selectPipeline(pipeline);
        });
    });

    // Execute query
    executeBtn.addEventListener('click', executeQuery);

    // Clear button
    clearBtn.addEventListener('click', clearAll);

    // Example chips
    exampleChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.dataset.query;
            if (query) {
                queryInput.value = query;
            }
        });
    });

    // Load DSL template
    loadDslTemplate.addEventListener('click', () => {
        const template = {
            "indices": "wazuh-alerts-*",
            "time": {
                "from": "now-24h",
                "to": "now",
                "timezone": "UTC"
            },
            "filters": [
                {
                    "field": "rule.level",
                    "op": "gte",
                    "value": 8
                }
            ],
            "must_not": [],
            "query_string": null,
            "aggregation": null,
            "limit": 50,
            "dry_run": false
        };
        dslInput.value = JSON.stringify(template, null, 2);
    });

    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });

    // Enter key to execute
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            executeQuery();
        }
    });
}

// Pipeline Selection
function selectPipeline(pipeline) {
    currentPipeline = pipeline;
    
    // Update button states
    pipelineBtns.forEach(btn => {
        if (btn.dataset.pipeline === pipeline) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Toggle input containers
    if (pipeline === 'dsl') {
        nlQueryContainer.classList.add('hidden');
        dslQueryContainer.classList.remove('hidden');
    } else {
        nlQueryContainer.classList.remove('hidden');
        dslQueryContainer.classList.add('hidden');
    }

    // Clear results
    hideAllStates();
}

// Execute Query
async function executeQuery() {
    const startTime = Date.now();
    
    // Validate input
    const query = currentPipeline === 'dsl' ? dslInput.value.trim() : queryInput.value.trim();
    if (!query) {
        showError('Please enter a query');
        return;
    }

    // Show loading state
    hideAllStates();
    loadingState.classList.remove('hidden');
    executeBtn.disabled = true;

    try {
        let endpoint, body;

        // Determine endpoint and body based on pipeline
        switch (currentPipeline) {
            case 'simple':
                endpoint = '/query/simple';
                body = { query: query };
                break;
            case 'advanced':
                endpoint = '/query/';
                body = { query: query };
                break;
            case 'dsl':
                endpoint = '/mcp/wazuh.search';
                try {
                    body = JSON.parse(query);
                } catch (e) {
                    throw new Error('Invalid JSON format');
                }
                break;
        }

        // Make API request
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });

        const endTime = Date.now();
        const executionTimeMs = endTime - startTime;

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Query failed');
        }

        const result = await response.json();
        lastQueryResult = result;

        // Display results
        displayResults(result, executionTimeMs);

    } catch (error) {
        console.error('Query error:', error);
        showError(error.message);
    } finally {
        executeBtn.disabled = false;
        loadingState.classList.add('hidden');
    }
}

// Display Results
function displayResults(result, executionTimeMs) {
    hideAllStates();
    successState.classList.remove('hidden');

    // Update metadata
    const count = extractResultCount(result);
    resultCount.textContent = count ? `${count} results` : '';
    executionTime.textContent = `${executionTimeMs}ms`;

    // Natural language response
    if (result.response) {
        nlResponse.classList.remove('hidden');
        nlResponseText.textContent = result.response;
    } else {
        nlResponse.classList.add('hidden');
    }

    // Formatted data
    displayFormattedData(result);

    // Raw JSON
    rawData.textContent = JSON.stringify(result, null, 2);

    // DSL (if available)
    if (result.dsl) {
        dslData.textContent = JSON.stringify(result.dsl, null, 2);
        document.querySelector('[data-tab="dsl"]').style.display = 'block';
    } else {
        document.querySelector('[data-tab="dsl"]').style.display = 'none';
    }

    // Switch to formatted tab
    switchTab('formatted');
}

// Display Formatted Data
function displayFormattedData(result) {
    formattedData.innerHTML = '';

    // Handle different response structures
    if (result.agents) {
        displayAgents(result.agents);
    } else if (result.alerts) {
        displayAlerts(result.alerts);
    } else if (result.raw_data) {
        if (result.raw_data.agents) {
            displayAgents(result.raw_data.agents);
        } else if (result.raw_data.alerts) {
            displayAlerts(result.raw_data.alerts);
        } else if (result.raw_data.hits) {
            displaySearchHits(result.raw_data.hits);
        }
    } else if (result.result) {
        // DSL query result
        if (result.result.hits) {
            displaySearchHits(result.result.hits);
        } else if (result.result.aggregations) {
            displayAggregations(result.result.aggregations);
        }
    }

    if (formattedData.innerHTML === '') {
        formattedData.innerHTML = '<p style="color: var(--text-secondary);">No formatted data available. Check Raw JSON tab.</p>';
    }
}

// Display Agents
function displayAgents(agents) {
    agents.forEach(agent => {
        const card = document.createElement('div');
        card.className = 'data-card';
        card.innerHTML = `
            <h4>Agent: ${agent.name}</h4>
            <div class="data-field">
                <span class="data-field-label">ID:</span>
                <span class="data-field-value">${agent.id}</span>
            </div>
            <div class="data-field">
                <span class="data-field-label">Status:</span>
                <span class="data-field-value">${agent.status || 'N/A'}</span>
            </div>
            <div class="data-field">
                <span class="data-field-label">IP:</span>
                <span class="data-field-value">${agent.ip || 'N/A'}</span>
            </div>
            <div class="data-field">
                <span class="data-field-label">OS:</span>
                <span class="data-field-value">${agent.os?.name || 'N/A'} ${agent.os?.version || ''}</span>
            </div>
            <div class="data-field">
                <span class="data-field-label">Last Keep Alive:</span>
                <span class="data-field-value">${agent.lastKeepAlive || 'N/A'}</span>
            </div>
        `;
        formattedData.appendChild(card);
    });
}

// Display Alerts
function displayAlerts(alerts) {
    alerts.forEach(alert => {
        const severity = getSeverityLevel(alert.rule?.level);
        const card = document.createElement('div');
        card.className = 'data-card';
        card.innerHTML = `
            <h4>${alert.rule?.description || 'Alert'}</h4>
            <div class="data-field">
                <span class="data-field-label">Rule ID:</span>
                <span class="data-field-value">${alert.rule?.id || 'N/A'}</span>
            </div>
            <div class="data-field">
                <span class="data-field-label">Severity:</span>
                <span class="data-field-value">
                    <span class="severity-badge severity-${severity}">${alert.rule?.level || 'N/A'} - ${severity.toUpperCase()}</span>
                </span>
            </div>
            <div class="data-field">
                <span class="data-field-label">Agent:</span>
                <span class="data-field-value">${alert.agent?.name || 'N/A'}</span>
            </div>
            <div class="data-field">
                <span class="data-field-label">Timestamp:</span>
                <span class="data-field-value">${alert.timestamp || alert['@timestamp'] || 'N/A'}</span>
            </div>
            ${alert.data?.srcip ? `
            <div class="data-field">
                <span class="data-field-label">Source IP:</span>
                <span class="data-field-value">${alert.data.srcip}</span>
            </div>
            ` : ''}
        `;
        formattedData.appendChild(card);
    });
}

// Display Search Hits
function displaySearchHits(hits) {
    const total = hits.total?.value || hits.total || 0;
    const results = hits.hits || [];

    const header = document.createElement('div');
    header.style.marginBottom = '20px';
    header.innerHTML = `<h4>Found ${total} matching records</h4>`;
    formattedData.appendChild(header);

    results.forEach(hit => {
        const source = hit._source;
        const card = document.createElement('div');
        card.className = 'data-card';
        
        const fields = [];
        
        // Prioritize common fields
        if (source.rule?.description) {
            fields.push(`<h4>${source.rule.description}</h4>`);
        }
        
        if (source.rule?.level) {
            const severity = getSeverityLevel(source.rule.level);
            fields.push(`
                <div class="data-field">
                    <span class="data-field-label">Severity:</span>
                    <span class="data-field-value">
                        <span class="severity-badge severity-${severity}">${source.rule.level} - ${severity.toUpperCase()}</span>
                    </span>
                </div>
            `);
        }
        
        if (source.agent?.name) {
            fields.push(`
                <div class="data-field">
                    <span class="data-field-label">Agent:</span>
                    <span class="data-field-value">${source.agent.name}</span>
                </div>
            `);
        }
        
        if (source['@timestamp']) {
            fields.push(`
                <div class="data-field">
                    <span class="data-field-label">Timestamp:</span>
                    <span class="data-field-value">${source['@timestamp']}</span>
                </div>
            `);
        }
        
        card.innerHTML = fields.join('');
        formattedData.appendChild(card);
    });
}

// Display Aggregations
function displayAggregations(aggregations) {
    const header = document.createElement('div');
    header.innerHTML = '<h4>Aggregation Results</h4>';
    formattedData.appendChild(header);

    Object.entries(aggregations).forEach(([key, value]) => {
        if (value.buckets) {
            const card = document.createElement('div');
            card.className = 'data-card';
            card.innerHTML = `
                <h4>${key}</h4>
                ${value.buckets.map(bucket => `
                    <div class="data-field">
                        <span class="data-field-label">${bucket.key}:</span>
                        <span class="data-field-value">${bucket.doc_count}</span>
                    </div>
                `).join('')}
            `;
            formattedData.appendChild(card);
        }
    });
}

// Helper Functions
function getSeverityLevel(level) {
    if (level >= 12) return 'critical';
    if (level >= 8) return 'high';
    if (level >= 5) return 'medium';
    return 'low';
}

function extractResultCount(result) {
    if (result.total) return result.total;
    if (result.agents) return result.agents.length;
    if (result.alerts) return result.alerts.length;
    if (result.raw_data?.hits?.total) {
        return result.raw_data.hits.total.value || result.raw_data.hits.total;
    }
    if (result.result?.hits?.total) {
        return result.result.hits.total.value || result.result.hits.total;
    }
    return null;
}

// UI State Management
function hideAllStates() {
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    successState.classList.add('hidden');
}

function showError(message) {
    hideAllStates();
    errorState.classList.remove('hidden');
    errorMessage.textContent = message;
}

function switchTab(tabName) {
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    tabPanes.forEach(pane => {
        if (pane.id === `${tabName}Tab`) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
}

function clearAll() {
    queryInput.value = '';
    dslInput.value = '';
    hideAllStates();
    resultCount.textContent = '';
    executionTime.textContent = '';
}

// Server Status Check
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        if (response.ok) {
            serverStatus.classList.add('online');
            serverStatusText.textContent = 'Server Online';
        } else {
            throw new Error('Server returned error');
        }
    } catch (error) {
        serverStatus.classList.add('offline');
        serverStatusText.textContent = 'Server Offline';
    }
}

// Check server status every 30 seconds
setInterval(checkServerStatus, 30000);
