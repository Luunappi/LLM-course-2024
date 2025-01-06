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

    function showToolInfo(tool) {
        fetch(`/tool_info/${tool}`)
            .then(response => response.json())
            .then(data => {
                toolInfo.innerHTML = `<h3>${tool}</h3><p>${data.info}</p>`;
                toolInfo.classList.add('active');
            })
            .catch(error => {
                console.error('Error:', error);
                toolInfo.innerHTML = `<h3>${tool}</h3><p>Error loading tool information</p>`;
                toolInfo.classList.add('active');
            });
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
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Käytä innerHTML assistentin viesteille, textContent käyttäjän viesteille
        if (role === 'assistant') {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        chatContent.appendChild(messageDiv);
        chatContent.scrollTop = chatContent.scrollHeight;
    }

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
        try {
            const response = await fetch('/api/tokens/stats');
            const data = await response.json();
            
            // Päivitä vain jos token-info on näkyvissä
            if (toolInfo.classList.contains('active')) {
                toolInfo.innerHTML = `
                    <h3>Token Usage</h3>
                    <div class="token-info">
                        <p><b>Current Message:</b> ${data.current.total_tokens} tokens</p>
                        <ul>
                            <li>Input: ${data.current.input_tokens}</li>
                            <li>Output: ${data.current.output_tokens}</li>
                            <li>Cost: $${data.current.cost.toFixed(4)}</li>
                        </ul>
                        <p><b>Session Total:</b> ${data.total.total_tokens} tokens ($${data.total.total_cost.toFixed(4)})</p>
                        <p><b>Per Model:</b></p>
                        <ul>
                            ${Object.entries(data.total.models).map(([model, stats]) => `
                                <li>${model}: ${stats.tokens} tokens ($${stats.cost.toFixed(4)})</li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error fetching token stats:', error);
            if (toolInfo.classList.contains('active')) {
                toolInfo.innerHTML = '<h3>Token Usage</h3><p>Error loading token information</p>';
            }
        }
    }
});