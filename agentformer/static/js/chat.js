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
            toolInfo.innerHTML = `
                <div class="tool-content">
                    <h3>System Settings</h3>
                    <p>Current system prompt: ${await getSystemPrompt()}</p>
                    <textarea id="system-prompt" rows="4" placeholder="Edit system prompt..."></textarea>
                    <button onclick="updateSystemPrompt()">Update</button>
                </div>
            `;
            toolInfo.classList.add('active');
            return;
        }

        // Prompt-napin käsittely
        if (tool === 'Prompt') {
            toolInfo.innerHTML = `
                <div class="tool-content">
                    <h3>Prompt Templates</h3>
                    <div class="prompt-templates">
                        <button onclick="usePrompt('analysis')">Analysis Template</button>
                        <button onclick="usePrompt('summary')">Summary Template</button>
                        <button onclick="usePrompt('code')">Code Template</button>
                    </div>
                </div>
            `;
            toolInfo.classList.add('active');
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
});