// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentPipeline = 'nl';
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
const routingInfo = document.getElementById('routingInfo');

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
            "index": "wazuh-alerts-*",
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": "now-24h",
                                    "lte": "now"
                                }
                            }
                        },
                        {
                            "range": {
                                "rule.level": {
                                    "gte": 8
                                }
                            }
                        }
                    ]
                }
            },
            "size": 50,
            "sort": [
                {
                    "timestamp": {
                        "order": "desc"
                    }
                }
            ]
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
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            executeQuery();
        }
    });
}

// Select pipeline
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

    // Show/hide appropriate containers
    if (pipeline === 'nl') {
        nlQueryContainer.classList.remove('hidden');
        nlQueryContainer.style.display = 'block';
        dslQueryContainer.classList.add('hidden');
        dslQueryContainer.style.display = 'none';
    } else if (pipeline === 'dsl') {
        nlQueryContainer.classList.add('hidden');
        nlQueryContainer.style.display = 'none';
        dslQueryContainer.classList.remove('hidden');
        dslQueryContainer.style.display = 'block';
    }

    clearAll();
}

// Execute query
async function executeQuery() {
    const startTime = Date.now();

    // Hide previous results
    hideAllStates();
    loadingState.classList.remove('hidden');
    loadingState.style.display = 'flex';

    try {
        let response;

        if (currentPipeline === 'nl') {
            // Natural Language query with intelligent routing
            const query = queryInput.value.trim();
            if (!query) {
                throw new Error('Please enter a query');
            }

            response = await fetch(`${API_BASE_URL}/query/nl`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });

        } else if (currentPipeline === 'dsl') {
            // Direct DSL query
            const dslText = dslInput.value.trim();
            if (!dslText) {
                throw new Error('Please enter a DSL query');
            }

            let dslObj;
            try {
                dslObj = JSON.parse(dslText);
            } catch (e) {
                throw new Error('Invalid JSON in DSL query');
            }

            response = await fetch(`${API_BASE_URL}/query/dsl`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dslObj),
            });
        }

        const endTime = Date.now();
        const executionTimeMs = endTime - startTime;

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const result = await response.json();
        lastQueryResult = result;

        // Display results
        displayResults(result, executionTimeMs);

    } catch (error) {
        console.error('Query error:', error);
        hideAllStates();
        errorState.classList.remove('hidden');
        errorState.style.display = 'block';
        errorMessage.textContent = error.message;
    }
}

// Display results
function displayResults(result, executionTimeMs) {
    console.log('Displaying results:', result);
    hideAllStates();
    successState.classList.remove('hidden');
    successState.style.display = 'block';

    // Update stats - handle both Indexer and API responses
    let totalHits = 0;
    if (result.raw_data?.hits?.total) {
        // Indexer response
        totalHits = result.raw_data.hits.total.value || result.raw_data.hits.total;
    } else if (result.raw_data?.data?.affected_items) {
        // Wazuh API response
        totalHits = result.raw_data.data.affected_items.length;
    } else if (result.raw_data?.total !== undefined) {
        // Alternative format
        totalHits = result.raw_data.total;
    }
    
    resultCount.textContent = totalHits;
    executionTime.textContent = `${executionTimeMs}ms`;

    // Display routing information (for NL queries)
    if (result.routing) {
        const routingHTML = `
            <div class="routing-badge">
                <span class="badge badge-${result.routing.pipeline === 'SIMPLE_PIPELINE' ? 'primary' : 'success'}">
                    ${result.routing.pipeline === 'SIMPLE_PIPELINE' ? '🔍 Simple Query' : '🚀 Advanced Query'}
                </span>
                <span class="confidence-badge">
                    Confidence: ${(result.routing.confidence * 100).toFixed(0)}%
                </span>
            </div>
            <div class="routing-reason">
                <strong>Routing Reason:</strong> ${result.routing.reasoning}
            </div>
        `;
        routingInfo.innerHTML = routingHTML;
        routingInfo.style.display = 'block';
    } else {
        routingInfo.style.display = 'none';
    }

    // Natural language summary (for NL queries)
    if (result.summary) {
        nlResponse.style.display = 'block';
        nlResponseText.textContent = result.summary;
    } else {
        nlResponse.style.display = 'none';
    }

    // Formatted data
    if (result.raw_data) {
        formattedData.innerHTML = displayFormattedData(result.raw_data);
    }

    // Raw JSON
    rawData.innerHTML = `<pre>${JSON.stringify(result.raw_data, null, 2)}</pre>`;

    // DSL Query (if available)
    if (result.dsl) {
        dslData.innerHTML = `<pre>${JSON.stringify(result.dsl, null, 2)}</pre>`;
    } else {
        dslData.innerHTML = '<pre>No DSL query (Simple API call)</pre>';
    }

    // Switch to formatted tab by default
    switchTab('formatted');
}

// Display formatted data
function displayFormattedData(rawData) {
    let html = '';

    // Handle Wazuh API response (agents)
    if (rawData.data?.affected_items) {
        const agents = rawData.data.affected_items;
        html = `
            <div class="agent-list">
                ${agents.map(agent => `
                    <div class="agent-card">
                        <div class="agent-header">
                            <span class="agent-id">ID: ${agent.id}</span>
                            <span class="status-badge status-${agent.status.toLowerCase()}">${agent.status}</span>
                        </div>
                        <div class="agent-info">
                            <div><strong>Name:</strong> ${agent.name}</div>
                            <div><strong>IP:</strong> ${agent.ip || 'N/A'}</div>
                            <div><strong>OS:</strong> ${agent.os?.name || 'N/A'} ${agent.os?.version || ''}</div>
                            <div><strong>Last Keep Alive:</strong> ${agent.lastKeepAlive || 'N/A'}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    // Handle Indexer response (alerts/logs)
    else if (rawData.hits?.hits) {
        const hits = rawData.hits.hits;
        html = `
            <div class="alert-list">
                ${hits.map(hit => {
                    const alert = hit._source;
                    return `
                        <div class="alert-card">
                            <div class="alert-header">
                                <span class="timestamp">${alert.timestamp || alert['@timestamp'] || 'N/A'}</span>
                                <span class="level-badge level-${alert.rule?.level >= 12 ? 'critical' : alert.rule?.level >= 8 ? 'high' : 'medium'}">
                                    Level ${alert.rule?.level || 'N/A'}
                                </span>
                            </div>
                            <div class="alert-rule">
                                <strong>${alert.rule?.description || 'Unknown rule'}</strong>
                            </div>
                            <div class="alert-details">
                                ${alert.agent?.name ? `<div><strong>Agent:</strong> ${alert.agent.name}</div>` : ''}
                                ${alert.data?.srcip ? `<div><strong>Source IP:</strong> ${alert.data.srcip}</div>` : ''}
                                ${alert.data?.dstip ? `<div><strong>Dest IP:</strong> ${alert.data.dstip}</div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    else {
        html = '<div class="no-data">No formatted data available</div>';
    }

    return html;
}

// Switch tab
function switchTab(tab) {
    // Update button states
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Show/hide panes
    tabPanes.forEach(pane => {
        if (pane.id === `${tab}Data`) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
}

// Clear all
function clearAll() {
    queryInput.value = '';
    dslInput.value = '';
    hideAllStates();
    lastQueryResult = null;
    nlResponse.style.display = 'none';
    routingInfo.style.display = 'none';
}

// Hide all states
function hideAllStates() {
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    successState.classList.add('hidden');
}

// Check server status
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            serverStatus.classList.remove('offline');
            serverStatus.classList.add('online');
            serverStatusText.textContent = 'Server Online';
        } else {
            throw new Error('Server returned error');
        }
    } catch (error) {
        serverStatus.classList.remove('online');
        serverStatus.classList.add('offline');
        serverStatusText.textContent = 'Server Offline';
    }

    // Check again in 5 seconds
    setTimeout(checkServerStatus, 5000);
}
