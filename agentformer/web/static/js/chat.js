// Quick questions - globaali funktio jotta HTML pääsee siihen käsiksi
window.setQuickQuestion = function(value) {
    if (value) {
        const messageInput = document.getElementById('message-input');
        messageInput.value = value;
        messageInput.focus();
        document.getElementById('quick-questions').value = '';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Initialize WebSocket and other setup...

    // DOM elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatContent = document.querySelector('.chat-content');
    const modeSwitch = document.getElementById('mode-switch');
    const modeLabel = document.querySelector('.toggle-label');

    // Mode toggle handling
    modeSwitch.addEventListener('change', function() {
        const isLLM = this.checked;
        modeLabel.textContent = isLLM ? 'LLM' : 'RAG';
        modeLabel.style.color = isLLM ? '#28a745' : '#007bff';
        console.log('Mode changed:', isLLM ? 'LLM' : 'RAG'); // Debug
    });

    // Set initial mode
    modeLabel.textContent = modeSwitch.checked ? 'LLM' : 'RAG';
    modeLabel.style.color = modeSwitch.checked ? '#28a745' : '#007bff';

    // Message handling
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        console.log('Sending message:', message); // Debug
        console.log('Mode:', modeSwitch.checked ? 'LLM' : 'RAG'); // Debug

        try {
            // Add user message
            addMessage(message, 'user');
            messageInput.value = '';

            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    mode: modeSwitch.checked  // true = LLM, false = RAG
                })
            });

            const data = await response.json();
            console.log('Response:', data); // Debug

            if (data.error) {
                addMessage(data.error, 'error');
            } else {
                addMessage(data.answer, 'assistant');
            }

        } catch (error) {
            console.error('Error:', error);
            addMessage('Error processing request', 'error');
        }
    }

    // Event listeners
    if (sendButton) {
        sendButton.onclick = sendMessage;
        console.log('Send button listener added'); // Debug
    }

    if (messageInput) {
        messageInput.onkeypress = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        };
        console.log('Message input listener added'); // Debug
    }

    // Helper functions
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        
        if (role === 'assistant') {
            const modelDiv = document.createElement('div');
            modelDiv.className = 'model-info';
            const mode = document.getElementById('mode-switch').checked;
            modelDiv.textContent = mode ? 'LLM: gpt-4o-mini' : 'RAG: gpt-4o-mini';
            messageDiv.appendChild(modelDiv);
        }
        
        chatContent.appendChild(messageDiv);
        chatContent.scrollTop = chatContent.scrollHeight;
    }

    // Tool button handling
    const toolButtons = document.querySelectorAll('.tool-button');
    const toolInfo = document.getElementById('tool-info');

    console.log('Found tool buttons:', toolButtons.length); // Debug
    console.log('Tool info element:', toolInfo); // Debug

    toolButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const tool = button.dataset.tool;
            console.log('Tool clicked:', tool, 'Button:', button); // Debug

            // Toggle active state
            const wasActive = button.classList.contains('active');
            toolButtons.forEach(btn => btn.classList.remove('active'));
            toolInfo.classList.remove('active');
            
            if (!wasActive) {
                button.classList.add('active');
                toolInfo.classList.add('active');
                
                try {
                    // Varmista oikea endpoint data-työkalulle
                    const endpoint = tool === 'data' ? '/api/tools/data' : `/api/tools/${tool}`;
                    console.log('Using endpoint:', endpoint); // Debug
                    
                    const response = await fetch(endpoint);
                    const data = await response.json();
                    console.log('Tool response:', data);

                    // Show tool info panel
                    toolInfo.innerHTML = '';
                    
                    if (tool === 'data') {
                        // Show file list
                        toolInfo.innerHTML = `
                            <h3>Files</h3>
                            <button class="reindex-button">Reindex All Files</button>
                            <div class="file-list">
                                ${data.files ? data.files.map(file => `
                                    <div class="file-item">
                                        <div class="file-name">${file.filename}</div>
                                        <div class="file-status">
                                            <i class="bi bi-check-circle"></i> Indexed
                                        </div>
                                    </div>
                                `).join('') : '<div class="no-files">No indexed files found</div>'}
                            </div>
                        `;
                    }
                    else if (tool === 'model') {
                        // Show model selection
                        toolInfo.innerHTML = `
                            <h3>Model Selection</h3>
                            <div class="model-list">
                                ${data.models.map(model => `
                                    <div class="model-item ${model.selected ? 'selected' : ''}" 
                                         data-model="${model.name}">
                                        <h4>${model.name}</h4>
                                        <p>${model.description}</p>
                                    </div>
                                `).join('')}
                            </div>
                        `;

                        // Add click handlers for model selection
                        const modelItems = toolInfo.querySelectorAll('.model-item');
                        modelItems.forEach(item => {
                            item.addEventListener('click', async () => {
                                const modelName = item.dataset.model;
                                try {
                                    const response = await fetch('/api/models/select', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ model: modelName })
                                    });
                                    const result = await response.json();
                                    if (result.status === 'success') {
                                        modelItems.forEach(m => m.classList.remove('selected'));
                                        item.classList.add('selected');
                                    }
                                } catch (error) {
                                    console.error('Error selecting model:', error);
                                }
                            });
                        });
                    }
                    else if (tool === 'tokens') {
                        // Show token usage
                        toolInfo.innerHTML = `
                            <h3>Token Usage</h3>
                            <div class="token-stats">
                                <div>Total: ${data.usage.total}</div>
                                <div>Last 24h: ${data.usage.last_24h}</div>
                                <div>Cost: ${data.usage.cost}</div>
                            </div>
                        `;
                    }
                    else if (tool === 'prompts') {
                        // Show prompt settings
                        toolInfo.innerHTML = `
                            <h3>Prompt Settings</h3>
                            <div class="prompt-settings">
                                <div class="system-prompt">
                                    <h4>System Prompt</h4>
                                    <textarea>${data.system_prompt}</textarea>
                                </div>
                                <div class="response-settings">
                                    <h4>Response Settings</h4>
                                    <div>Length: ${data.response_length} words</div>
                                    <div>Temperature: ${data.temperature}</div>
                                </div>
                            </div>
                        `;
                    }

                } catch (error) {
                    console.error('Error fetching tool info:', error);
                }
            }
        });
    });

    // Add reindex button handler
    toolInfo.addEventListener('click', async (e) => {
        if (e.target.classList.contains('reindex-button')) {
            try {
                const response = await fetch('/api/rag/reindex', {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.status === 'success') {
                    // Refresh file list
                    const dataButton = document.querySelector('[data-tool="data"]');
                    if (dataButton) dataButton.click();
                }
            } catch (error) {
                console.error('Error reindexing:', error);
            }
        }
    });
});