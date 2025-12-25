// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentPipeline = 'nl';
let lastQueryResult = null;

// Markdown to HTML converter (simple implementation)
function markdownToHtml(markdown) {
    if (!markdown) return '';
    
    let html = markdown
        // Escape HTML first
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Lists (bullets)
        .replace(/^\s*[-*]\s+(.*)$/gm, '<li>$1</li>')
        // Code blocks
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // Wrap lists in <ul>
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    
    // Wrap in paragraph if not already wrapped
    if (!html.startsWith('<h') && !html.startsWith('<ul') && !html.startsWith('<pre')) {
        html = '<p>' + html + '</p>';
    }
    
    return html;
}

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
        
        let errorText = error.message;
        if (error.message.includes('HTTP')) {
            errorText += '\n\nPossible causes:\n';
            errorText += '- Invalid field names in query\n';
            errorText += '- Time window too large\n';
            errorText += '- Authentication failed\n';
            errorText += '\nCheck server logs for details.';
        }
        errorMessage.textContent = errorText;
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
    if (result.total_hits !== undefined) {
        // Direct from response
        totalHits = result.total_hits;
    } else if (result.raw_data?.hits?.total) {
        // Indexer response
        totalHits = result.raw_data.hits.total.value || result.raw_data.hits.total;
    } else if (result.raw_results?.hits?.total) {
        // Alternative Indexer response
        totalHits = result.raw_results.hits.total.value || result.raw_results.hits.total;
    } else if (result.raw_data?.data?.affected_items) {
        // Wazuh API response
        totalHits = result.raw_data.data.affected_items.length;
    } else if (result.raw_data?.total !== undefined) {
        // Alternative format
        totalHits = result.raw_data.total;
    }

    resultCount.textContent = `${totalHits} results`;
    executionTime.textContent = result.query_time || `${executionTimeMs}ms`;

    // Show routing information
    if (result.routing) {
        displayRoutingInfo(result.routing);
    } else if (result.pipeline === 'DIRECT_DSL') {
        displayRoutingInfo({
            pipeline: 'DIRECT_DSL',
            confidence: 1.0,
            reasoning: 'Direct DSL query executed without routing'
        });
    } else if (result.pipeline === 'HYBRID_NL_DSL') {
        displayRoutingInfo({
            pipeline: 'HYBRID_NL_DSL',
            confidence: 1.0,
            reasoning: result.routing?.reasoning || 'Embedded DSL with natural language context'
        });
    }

    // Show NL context for hybrid queries
    if (result.pipeline === 'HYBRID_NL_DSL' && result.nl_context) {
        const existingRoutingDiv = document.querySelector('.routing-info');
        
        // Remove any existing NL context display
        const existingContext = document.querySelector('.nl-context-section');
        if (existingContext) {
            existingContext.remove();
        }
        
        const nlContextDiv = document.createElement('div');
        nlContextDiv.className = 'nl-context-section';
        nlContextDiv.innerHTML = `
            <strong>📝 Natural Language Context:</strong>
            <p>${result.nl_context}</p>
        `;
        
        if (existingRoutingDiv && existingRoutingDiv.nextSibling) {
            existingRoutingDiv.parentNode.insertBefore(nlContextDiv, existingRoutingDiv.nextSibling);
        } else if (existingRoutingDiv) {
            existingRoutingDiv.after(nlContextDiv);
        }
    }

    // Show summary/natural language response
    if (result.summary || result.formatted_response) {
        nlResponse.classList.remove('hidden');
        nlResponse.style.display = 'block';
        nlResponseText.innerHTML = markdownToHtml(result.summary || result.formatted_response);
    } else {
        nlResponse.classList.add('hidden');
        nlResponse.style.display = 'none';
    }
    
    resultCount.textContent = totalHits;
    executionTime.textContent = `${executionTimeMs}ms`;

    // Display routing information
    if (result.routing) {
        const pipelineMap = {
            'SIMPLE_PIPELINE': { name: 'Simple', icon: '🔍', color: 'primary' },
            'ADVANCED_PIPELINE': { name: 'Advanced', icon: '🚀', color: 'success' },
            'DIRECT_DSL': { name: 'Direct DSL', icon: '⚡', color: 'warning' },
            'HYBRID_NL_DSL': { name: 'Hybrid NL+DSL', icon: '🔬', color: 'info' }
        };
        
        const pipeline = result.routing.pipeline || result.pipeline;
        const pipelineInfo = pipelineMap[pipeline] || { name: pipeline, icon: '❓', color: 'secondary' };
        const confidencePercent = (result.routing.confidence * 100).toFixed(0);
        
        let routingHTML = `
            <div class="routing-header">
                <div class="routing-badge">
                    <span class="badge badge-${pipelineInfo.color}">
                        ${pipelineInfo.icon} ${pipelineInfo.name} Pipeline
                    </span>
                    <span class="confidence-badge" style="background: ${confidencePercent >= 90 ? '#10b981' : confidencePercent >= 70 ? '#f59e0b' : '#ef4444'}">
                        ${confidencePercent}% Confidence
                    </span>
                </div>
            </div>
            <div class="routing-details">
                <div class="routing-reason">
                    <strong>📋 Routing Reason:</strong> ${result.routing.reasoning}
                </div>`;
        
        // Show parsed query details for advanced pipeline
        if (result.parsed_query && pipeline === 'ADVANCED_PIPELINE') {
            const pq = result.parsed_query;
            routingHTML += `
                <div class="parsed-query-info">
                    <strong>🔧 Query Details:</strong>
                    <ul>
                        ${pq.filters && pq.filters.length > 0 ? `<li>Filters: ${pq.filters.length} active</li>` : ''}
                        ${pq.time ? `<li>Time: ${pq.time.from} to ${pq.time.to}</li>` : ''}
                        ${pq.limit ? `<li>Limit: ${pq.limit} results</li>` : ''}
                        ${pq.aggregation ? `<li>Aggregation: ${pq.aggregation.type}</li>` : ''}
                    </ul>
                </div>`;
        }
        
        routingHTML += `</div>`;
        routingInfo.innerHTML = routingHTML;
        routingInfo.style.display = 'block';
    } else {
        routingInfo.style.display = 'none';
    }

    // Natural language summary (for NL queries)
    if (result.summary) {
        nlResponse.style.display = 'block';
        nlResponseText.innerHTML = markdownToHtml(result.summary);
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

// Display routing information
function displayRoutingInfo(routing) {
    if (!routingInfo) return;

    const pipelineMap = {
        'SIMPLE_PIPELINE': { name: 'Simple (Wazuh API)', icon: '🔍', color: 'primary' },
        'ADVANCED_PIPELINE': { name: 'Advanced (Wazuh Indexer)', icon: '🚀', color: 'success' },
        'DIRECT_DSL': { name: 'Direct DSL (No Routing)', icon: '⚡', color: 'warning' },
        'HYBRID_NL_DSL': { name: 'Hybrid NL+DSL (AI Analysis)', icon: '🔬', color: 'info' }
    };

    const pipeline = routing.pipeline;
    const pipelineInfo = pipelineMap[pipeline] || { name: pipeline, icon: '❓', color: 'secondary' };
    const confidence = routing.confidence || 0;
    const confidencePercent = Math.round(confidence * 100);
    
    // Determine confidence color
    let confidenceColor = '#ef4444'; // red
    if (confidencePercent >= 90) confidenceColor = '#10b981'; // green
    else if (confidencePercent >= 70) confidenceColor = '#f59e0b'; // yellow

    routingInfo.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <div>
                <span style="font-size: 1.2em;">${pipelineInfo.icon}</span>
                <strong>${pipelineInfo.name}</strong>
            </div>
            <span class="confidence-badge" style="background: ${confidenceColor}; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: 600; color: white;">
                ${confidencePercent}% confidence
            </span>
        </div>
        <div style="color: var(--text-secondary); font-size: 0.9em;">
            ${routing.reasoning || 'No reasoning provided'}
        </div>
    `;
    
    routingInfo.style.display = 'block';
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
