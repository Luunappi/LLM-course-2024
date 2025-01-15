document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const toolButtons = document.querySelectorAll('.tool-button');
    const toolInfo = document.getElementById('tool-info');
    const modelButton = document.querySelector('.tool-button[data-tool="model"]');
    const modelDropdown = document.getElementById('model-dropdown');

    // Tool buttons
    toolButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Jos nappi on jo aktiivinen, poista info ja aktiivinen tila
            if (this.classList.contains('active')) {
                this.classList.remove('active');
                toolInfo.classList.remove('active');
                return;
            }
            
            // Poista active-luokka kaikilta
            toolButtons.forEach(btn => btn.classList.remove('active'));
            
            // Jos kyseessä on mallinappi, älä näytä tool infoa
            if (this.dataset.tool === 'model') {
                toolInfo.classList.remove('active');
                return;
            }
            
            // Lisää active-luokka klikatulle
            this.classList.add('active');

            if (this.classList.contains('upload-icon')) {
                handleUpload();
            } else if (this.classList.contains('web-icon')) {
                handleWebSearch();
            } else if (this.textContent.trim() === 'Tokens') {
                showTokenInfo();
            } else {
                const tool = this.textContent.trim();
                showToolInfo(tool);
            }
        });
    });

    function handleWebSearch() {
        toolInfo.innerHTML = `
            <h3>Web Search</h3>
            <div class="web-search-input">
                <input type="text" id="url-input" placeholder="Enter URL to crawl...">
                <button onclick="startCrawling()">Start</button>
            </div>
        `;
        toolInfo.classList.add('active');
    }

    function startCrawling() {
        const url = document.getElementById('url-input').value.trim();
        if (url) {
            fetch('/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                toolInfo.innerHTML = `<h3>Crawling Results</h3><p>${data.results}</p>`;
            });
        }
    }

    async function showToolInfo(tool) {
        const toolInfo = document.getElementById('tool-info');
        
        // Tokens-napin erikoiskäsittely
        if (tool === 'Tokens') {
            await showTokenInfo();
            return;
        }

        // System-napin käsittely
        if (tool === 'System') {
            try {
                const systemStats = await fetch('/api/system/stats').then(r => r.json());
                
                toolInfo.innerHTML = `
                    <div class="tool-content">
                        <h3>System Information</h3>
                        
                        <div class="system-section">
                            <h4>Performance Metrics</h4>
                            <div class="metrics-grid">
                                <div class="metric">
                                    <div class="metric-value">${systemStats.total_time.toFixed(2)}s</div>
                                    <div class="metric-label">Total Processing Time</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${systemStats.steps.length}</div>
                                    <div class="metric-label">Processing Steps</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${systemStats.model_used || 'N/A'}</div>
                                    <div class="metric-label">Current Model</div>
                                </div>
                            </div>
                        </div>

                        <div class="system-section">
                            <h4>Memory Usage</h4>
                            <div class="metrics-grid">
                                <div class="metric">
                                    <div class="metric-value">${Math.round(systemStats.additional_metrics.memory_usage.rss)}MB</div>
                                    <div class="metric-label">RSS Memory</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${Math.round(systemStats.additional_metrics.memory_usage.vms)}MB</div>
                                    <div class="metric-label">Virtual Memory</div>
                                </div>
                            </div>
                        </div>

                        <div class="system-section">
                            <h4>Active Components</h4>
                            <div class="component-list">
                                ${systemStats.additional_metrics.active_components.map(comp => 
                                    `<div class="component-item">${comp}</div>`
                                ).join('')}
                            </div>
                        </div>

                        ${systemStats.steps.length > 0 ? `
                            <div class="system-section">
                                <h4>Processing Steps</h4>
                                <div class="steps-timeline">
                                    ${systemStats.steps.map(step => `
                                        <div class="timeline-item">
                                            <div class="step-time">${step.time.toFixed(2)}s</div>
                                            <div class="step-name">${step.step}</div>
                                            ${step.details ? `
                                                <div class="step-details">
                                                    ${Object.entries(step.details).map(([key, value]) => 
                                                        `<div>${key}: ${value}</div>`
                                                    ).join('')}
                                                </div>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
                toolInfo.classList.add('active');
            } catch (error) {
                console.error('Error loading system info:', error);
                toolInfo.innerHTML = `
                    <div class="tool-content">
                        <h3>System Information</h3>
                        <p>Error loading system information</p>
                    </div>
                `;
                toolInfo.classList.add('active');
            }
            return;
        }

        // Lisää Debug-napin käsittely
        if (tool === 'Debug') {
            try {
                const debugInfo = await fetch('/api/debug/info').then(r => r.json());
                
                toolInfo.innerHTML = `
                    <div class="tool-content">
                        <h3>Debug Information</h3>
                        
                        <div class="debug-stats">
                            <div class="stat-item">
                                <span class="stat-label">Total Events:</span>
                                <span class="stat-value">${debugInfo.stats.total_events}</span>
                            </div>
                            <div class="stat-item error">
                                <span class="stat-label">Errors:</span>
                                <span class="stat-value">${debugInfo.stats.error_count}</span>
                            </div>
                            <div class="stat-item warning">
                                <span class="stat-label">Warnings:</span>
                                <span class="stat-value">${debugInfo.stats.warning_count}</span>
                            </div>
                        </div>

                        <div class="debug-events">
                            <h4>Recent Events</h4>
                            ${debugInfo.events.map(event => `
                                <div class="debug-event ${event.level.toLowerCase()}">
                                    <div class="event-header">
                                        <span class="event-time">${event.timestamp}</span>
                                        <span class="event-level">${event.level}</span>
                                        <span class="event-component">${event.component}</span>
                                    </div>
                                    <div class="event-message">${event.message}</div>
                                    ${event.details ? `
                                        <div class="event-details">
                                            <pre>${JSON.stringify(event.details, null, 2)}</pre>
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                toolInfo.classList.add('active');
            } catch (error) {
                console.error('Error loading debug info:', error);
                toolInfo.innerHTML = `
                    <div class="tool-content">
                        <h3>Debug Information</h3>
                        <p>Error loading debug information</p>
                    </div>
                `;
                toolInfo.classList.add('active');
            }
            return;
        }

        // Prompt-napin käsittely
        if (tool === 'Prompt') {
            try {
                const response = await fetch('/api/prompts');
                const data = await response.json();
                
                toolInfo.innerHTML = `
                    <div class="tool-content">
                        <h3>Prompt Settings</h3>
                        
                        <div class="prompt-section">
                            <h4>System Prompts</h4>
                            <div class="prompt-list">
                                ${Object.entries(data.prompts.system).map(([name, content]) => `
                                    <div class="prompt-item">
                                        <div class="prompt-name">${name}</div>
                                        <textarea class="prompt-editor" 
                                            data-type="system" 
                                            data-name="${name}"
                                            oninput="autoSavePrompt(this)">${content}</textarea>
                                        <div class="prompt-actions">
                                            <button onclick="resetPrompt('system', '${name}')" 
                                                    class="prompt-reset">Reset to Default</button>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <div class="prompt-section">
                            <h4>Tool Prompts</h4>
                            <div class="prompt-list">
                                ${Object.entries(data.prompts.tool).map(([name, content]) => `
                                    <div class="prompt-item">
                                        <div class="prompt-name">${name}</div>
                                        <textarea class="prompt-editor" 
                                            data-type="tool" 
                                            data-name="${name}"
                                            oninput="autoSavePrompt(this)">${content}</textarea>
                                        <div class="prompt-actions">
                                            <button onclick="resetPrompt('tool', '${name}')" 
                                                    class="prompt-reset">Reset to Default</button>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <div class="prompt-section">
                            <h4>Response Length</h4>
                            <div class="slider-container">
                                <input type="range" id="max-words" 
                                       min="10" max="250" value="50" step="10"
                                       oninput="updateWordLimit(this.value)">
                                <span id="word-limit-value">50 words</span>
                            </div>
                        </div>
                    </div>
                `;
                toolInfo.classList.add('active');
            } catch (error) {
                console.error('Error loading prompts:', error);
                toolInfo.innerHTML = `
                    <div class="tool-content">
                        <h3>Prompt Settings</h3>
                        <p>Error loading prompt information</p>
                    </div>
                `;
                toolInfo.classList.add('active');
            }
            return;
        }

        // Muiden työkalujen käsittely
        try {
            const response = await fetch(`/api/tool_info/${tool.toLowerCase()}`);
            const data = await response.json();
            if (data.info) {
                toolInfo.innerHTML = `<h3>${tool}</h3><p>${data.info}</p>`;
                toolInfo.classList.add('active');
            }
        } catch (error) {
            console.error('Error loading tool info:', error);
            toolInfo.innerHTML = `<h3>${tool}</h3><p>Error loading tool information</p>`;
            toolInfo.classList.add('active');
        }
    }

    function handleUpload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.txt,.pdf,.doc,.docx';
        input.onchange = function(e) {
            const file = e.target.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                toolInfo.innerHTML = `<h3>Upload</h3><p>${data.message}</p>`;
                toolInfo.classList.add('active');
            });
        };
        input.click();
    }

    // Send message
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (message && !sendButton.classList.contains('loading')) {
            try {
                // Näytä loading-tila
                sendButton.classList.add('loading');
                sendButton.innerHTML = '';
                
                // Lisää viesti chatiin heti
                appendMessage('user', message);
                messageInput.value = '';

                const controller = new AbortController();
                const signal = controller.signal;
                
                // Lisää stop-toiminnallisuus
                sendButton.onclick = () => {
                    controller.abort();
                    resetSendButton();
                };

                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message
                    }),
                    signal
                });

                const data = await response.json();
                console.log('Response from server:', data);
                if (data.response) {
                    appendMessage('assistant', data.response);
                    
                    // Päivitä token-tiedot jos token-info on näkyvissä
                    if (document.querySelector('.tool-button[data-tool="tokens"]').classList.contains('active')) {
                        await showTokenInfo();
                    }
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    appendMessage('error', 'Message cancelled');
                } else {
                    console.error('Error sending message:', error);
                    appendMessage('error', 'Error sending message. Please try again.');
                }
            } finally {
                resetSendButton();
            }
        }
    }

    // Funktio send-napin palauttamiseen normaalitilaan
    function resetSendButton() {
        sendButton.classList.remove('loading');
        sendButton.textContent = 'Send';
        sendButton.onclick = sendMessage;
    }

    // Lisätään funktio viestien näyttämiseen
    function appendMessage(role, content) {
        const chatContent = document.querySelector('.chat-content');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Generoi uniikki ID viestille
        const messageId = Date.now();
        messageDiv.dataset.messageId = messageId;
        
        // Lisää poisto-nappi
        if (role !== 'error') {
            const deleteButton = document.createElement('button');
            deleteButton.className = 'delete-message';
            deleteButton.innerHTML = '×';
            deleteButton.onclick = () => deleteMessage(messageId);
            messageDiv.appendChild(deleteButton);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'assistant') {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        chatContent.appendChild(messageDiv);
        chatContent.scrollTop = chatContent.scrollHeight;
    }

    // Lisää viestin poistamisen käsittely
    async function deleteMessage(messageId) {
        try {
            const response = await fetch(`/api/chat/message/${messageId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (data.status === 'success') {
                const messageElements = document.querySelectorAll(`[data-message-id="${messageId}"]`);
                messageElements.forEach(el => el.remove());
            }
        } catch (error) {
            console.error('Error deleting message:', error);
        }
    }

    // Lisää historian tyhjennyksen käsittely
    document.querySelector('.clear-history').addEventListener('click', async (e) => {
        e.stopPropagation();
        
        // Tarkista onko dialogi jo olemassa
        let dialog = document.querySelector('.confirm-dialog');
        if (!dialog) {
            dialog = document.createElement('div');
            dialog.className = 'confirm-dialog';
            dialog.innerHTML = `
                <div>Are you sure you want to delete all messages?</div>
                <div class="confirm-dialog-buttons">
                    <button class="confirm-button cancel">Cancel</button>
                    <button class="confirm-button confirm">Delete</button>
                </div>
            `;
            document.body.appendChild(dialog);
            
            // Lisää click handlerit napeille
            dialog.querySelector('.confirm-button.confirm').onclick = async () => {
                try {
                    const response = await fetch('/api/chat/history', {
                        method: 'DELETE'
                    });
                    const data = await response.json();
                    if (data.status === 'success') {
                        document.querySelector('.chat-content').innerHTML = '';
                    }
                } catch (error) {
                    console.error('Error clearing history:', error);
                }
                dialog.classList.remove('show');
            };
            
            dialog.querySelector('.confirm-button.cancel').onclick = () => {
                dialog.classList.remove('show');
            };
            
            // Sulje dialogi kun klikataan muualle
            document.addEventListener('click', (e) => {
                if (!dialog.contains(e.target) && !e.target.matches('.clear-history')) {
                    dialog.classList.remove('show');
                }
            });
        }
        
        dialog.classList.add('show');
    });

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Alusta mallit kun sivu latautuu
    initializeModels();
    
    async function initializeModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            
            // Päivitä mallinappi
            updateModelButton(data.current);
            
            // Luo mallivaihtoehdot dropdowniin
            modelDropdown.innerHTML = '';
            
            const modelDescriptions = {
                'gpt-4o': 'Great for most tasks',
                'o1': 'Uses advanced reasoning',
                'o1-mini': 'Faster at reasoning',
                'gpt-4o-mini': 'Fast and cost-effective'
            };
            
            data.models.forEach(model => {
                const option = document.createElement('div');
                option.className = 'model-option';
                if (model.name === data.current.name) {
                    option.classList.add('selected');
                }
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'model-name';
                nameSpan.textContent = model.display_name;
                
                const descSpan = document.createElement('span');
                descSpan.className = 'model-description';
                descSpan.textContent = modelDescriptions[model.name] || '';
                
                option.appendChild(nameSpan);
                option.appendChild(descSpan);
                
                option.addEventListener('click', async () => {
                    document.querySelectorAll('.model-option').forEach(opt => {
                        opt.classList.remove('selected');
                    });
                    option.classList.add('selected');
                    await selectModel(model.name);
                    modelDropdown.classList.remove('show');
                });
                
                modelDropdown.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error initializing models:', error);
        }
    }
    
    function updateModelButton(model) {
        modelButton.textContent = model.button_name;
    }
    
    async function selectModel(modelName) {
        try {
            const response = await fetch('/api/models/select', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: modelName })
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                updateModelButton(data.model);
            }
        } catch (error) {
            console.error('Error selecting model:', error);
        }
    }
    
    // Näytä/piilota dropdown kun mallinappia klikataan
    modelButton.addEventListener('click', (e) => {
        e.stopPropagation();
        modelDropdown.classList.toggle('show');
    });
    
    // Piilota dropdown kun klikataan muualle
    document.addEventListener('click', () => {
        modelDropdown.classList.remove('show');
    });

    // Lisää mikrofonin click handler
    document.querySelector('.input-icon').addEventListener('click', function() {
        alert('Voice input feature under construction - coming soon!');
    });

    // Lisää token-tietojen näyttö
    async function showTokenInfo() {
        const toolInfo = document.getElementById('tool-info');
        try {
            const response = await fetch('/api/tokens/stats');
            const data = await response.json();
            
            toolInfo.innerHTML = `
                <div class="token-info">
                    <h3>Token Usage</h3>
                    <div class="current-usage">
                        <h4>Current Message</h4>
                        <ul>
                            <li>Input: <b>${data.current.input_tokens || 0}</b> tokens</li>
                            <li>Output: <b>${data.current.output_tokens || 0}</b> tokens</li>
                            <li>Total: <b>${data.current.total_tokens || 0}</b> tokens</li>
                            <li>Cost: <b>$${(data.current.cost || 0).toFixed(4)}</b></li>
                        </ul>
                    </div>
                    <div class="total-usage">
                        <h4>Session Total</h4>
                        <p><b>${data.total.total_tokens || 0}</b> tokens ($${(data.total.total_cost || 0).toFixed(4)})</p>
                        <h4>Per Model</h4>
                        <ul>
                            ${Object.entries(data.total.models || {}).map(([model, stats]) => `
                                <li>${model}: <b>${stats.tokens}</b> tokens ($${stats.cost.toFixed(4)})</li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
            toolInfo.classList.add('active');
        } catch (error) {
            console.error('Error fetching token stats:', error);
            toolInfo.innerHTML = `
                <div class="token-info">
                    <h3>Token Usage</h3>
                    <p>Error loading token information</p>
                </div>
            `;
            toolInfo.classList.add('active');
        }
    }

    // Lisätään apufunktiot system promptin käsittelyyn
    async function getSystemPrompt() {
        try {
            const response = await fetch('/api/system/prompt');
            const data = await response.json();
            return data.prompt || 'Default system prompt';
        } catch (error) {
            console.error('Error getting system prompt:', error);
            return 'Error loading system prompt';
        }
    }

    async function updateSystemPrompt() {
        const newPrompt = document.getElementById('system-prompt').value;
        try {
            const response = await fetch('/api/system/prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: newPrompt })
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToolInfo('System'); // Päivitä näkymä
            }
        } catch (error) {
            console.error('Error updating system prompt:', error);
        }
    }

    // Lisätään prompt template -funktiot
    function usePrompt(template) {
        const messageInput = document.getElementById('message-input');
        const templates = {
            analysis: "Please analyze the following:\n\n",
            summary: "Please provide a summary of:\n\n",
            code: "Please help me with this code:\n\n"
        };
        messageInput.value = templates[template] || '';
        messageInput.focus();
    }

    // Lisää uudet apufunktiot
    async function setPrompt(type, name) {
        try {
            const response = await fetch('/api/prompts/set', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ type, name })
            });
            const data = await response.json();
            if (data.status === 'success') {
                // Näytä pieni ilmoitus onnistumisesta
                const button = event.target;
                const originalText = button.textContent;
                button.textContent = 'Active';
                button.classList.add('active');
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('active');
                }, 1500);
            }
        } catch (error) {
            console.error('Error setting prompt:', error);
        }
    }

    function updateWordLimit(value) {
        document.getElementById('word-limit-value').textContent = `${value} words`;
        // Tallenna arvo backendille
        fetch('/api/settings/word_limit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ limit: parseInt(value) })
        }).catch(error => console.error('Error updating word limit:', error));
    }

    // Lisää uudet funktiot promptien käsittelyyn
    let saveTimeout;

    async function autoSavePrompt(textarea) {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(async () => {
            const type = textarea.dataset.type;
            const name = textarea.dataset.name;
            const content = textarea.value;
            
            try {
                const response = await fetch('/api/prompts/set', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ type, name, content })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    // Näytä pieni tallennusindikaattori
                    const indicator = document.createElement('div');
                    indicator.className = 'save-indicator';
                    indicator.textContent = 'Saved';
                    textarea.parentNode.appendChild(indicator);
                    setTimeout(() => indicator.remove(), 1500);
                }
            } catch (error) {
                console.error('Error saving prompt:', error);
            }
        }, 1000); // Odota 1 sekunti ennen tallennusta
    }

    async function resetPrompt(type, name) {
        try {
            const response = await fetch('/api/prompts/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ type, name })
            });
            const data = await response.json();
            if (data.status === 'success') {
                // Päivitä textarea
                const textarea = document.querySelector(
                    `.prompt-editor[data-type="${type}"][data-name="${name}"]`
                );
                if (textarea) {
                    textarea.value = data.prompt;
                }
            }
        } catch (error) {
            console.error('Error resetting prompt:', error);
        }
    }

    async function updateDebugStatus() {
        try {
            const debugInfo = await fetch('/api/debug/info').then(r => r.json());
            const debugButton = document.querySelector('.tool-button[data-tool="debug"]');
            
            if (debugInfo.stats.error_count > 0) {
                debugButton.classList.add('has-errors');
                debugButton.dataset.count = debugInfo.stats.error_count;
            } else {
                debugButton.classList.remove('has-errors');
                debugButton.removeAttribute('data-count');
            }
        } catch (error) {
            console.error('Error updating debug status:', error);
        }
    }

    // Päivitä debug-status säännöllisesti
    setInterval(updateDebugStatus, 5000);

    // Päivitä myös heti kun sivu latautuu
    document.addEventListener('DOMContentLoaded', updateDebugStatus);
});