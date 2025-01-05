document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        messageDiv.textContent = message;
        
        // Lisää viesti alimmaksi
        chatMessages.appendChild(messageDiv);
        
        // Vieritä chat aina alas uusimman viestin kohdalle
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        messageInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            if (data.error) {
                addMessage('Error: ' + data.error);
            } else {
                addMessage(data.response);
                await updateTokenInfo(data);
            }
        } catch (error) {
            addMessage('Error sending message: ' + error.message);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Korjaa upload-napin valinta
    const uploadButton = document.querySelector('.input-group .bi-upload').parentElement;
    if (uploadButton) {
        uploadButton.addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf,.txt,.md';
            input.style.display = 'none';
            
            input.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        uploadButton.disabled = true;
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        if (result.success) {
                            addMessage(`File ${file.name} uploaded successfully`);
                        } else {
                            addMessage(`Failed to upload ${file.name}: ${result.error}`);
                        }
                    } catch (error) {
                        addMessage('Error uploading file: ' + error.message);
                    } finally {
                        uploadButton.disabled = false;
                    }
                }
            });
            
            document.body.appendChild(input);
            input.click();
            document.body.removeChild(input);
        });
    }

    // Korjaa token-laskurin päivitys
    async function updateTokenInfo(data) {
        const tokenCount = document.getElementById('token-count');
        const tokenCost = document.getElementById('token-cost');
        
        if (!tokenCount || !tokenCost) return;
        
        try {
            // Jos token_usage ei tule suoraan vastauksessa, haetaan se erikseen
            if (!data.token_usage && data.response) {
                const response = await fetch('/calculate_tokens', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: data.response })
                });
                const tokenData = await response.json();
                data.token_usage = tokenData.token_usage;
            }
            
            if (data.token_usage) {
                const {input_tokens = 0, output_tokens = 0, total_tokens = 0, cost = 0} = data.token_usage;
                tokenCount.textContent = `${total_tokens} tokens used (${input_tokens} in, ${output_tokens} out)`;
                tokenCost.textContent = `Cost: $${cost.toFixed(4)}`;
            }
        } catch (error) {
            console.error('Error updating token info:', error);
        }
    }

    // Model selector handling
    const modelBtn = document.getElementById('model-select-btn');
    const modelDropdown = document.getElementById('model-dropdown');
    const modelName = modelBtn.querySelector('.model-name');

    if (modelBtn) {
        modelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            // Toggle dropdown
            const isVisible = modelDropdown.style.display === 'block';
            modelDropdown.style.display = isVisible ? 'none' : 'block';
            
            // Sulje muut paneelit
            document.querySelectorAll('.info-panel').forEach(panel => {
                panel.style.display = 'none';
            });
            document.querySelectorAll('.info-button').forEach(btn => {
                btn.classList.remove('active');
            });
        });
    }

    // Handle model selection
    document.querySelectorAll('.model-option').forEach(option => {
        option.addEventListener('click', async () => {
            const selectedModel = option.dataset.model;
            const selectedName = option.textContent;
            
            try {
                const response = await fetch('/switch_model', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ model: selectedModel })
                });
                
                const data = await response.json();
                if (data.success) {
                    modelName.textContent = selectedName;
                    modelDropdown.style.display = 'none';
                    addMessage(`Switched to ${selectedName} model`);
                } else {
                    addMessage('Failed to switch model: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                addMessage('Error switching model: ' + error.message);
            }
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        if (modelDropdown) {
            modelDropdown.style.display = 'none';
        }
    });
});

// Info panel handling
const infoPanels = ['token', 'system', 'prompt', 'document'];

infoPanels.forEach(type => {
    document.getElementById(`${type}-info-btn`).addEventListener('click', () => {
        toggleInfoPanel(type);
    });
});

function toggleInfoPanel(type) {
    const allPanels = document.querySelectorAll('.info-panel');
    const allButtons = document.querySelectorAll('.info-button');
    const button = document.getElementById(`${type}-info-btn`);
    const panel = document.getElementById(`${type}-info-panel`);
    
    // Jos paneeli on jo auki, suljetaan se
    if (button.classList.contains('active')) {
        button.classList.remove('active');
        panel.style.display = 'none';
        return;
    }
    
    // Muuten suljetaan kaikki ja avataan valittu
    allButtons.forEach(btn => btn.classList.remove('active'));
    allPanels.forEach(p => p.style.display = 'none');
    
    button.classList.add('active');
    panel.style.display = 'block';
    
    // Jos kyseessä on prompt-paneeli, alustetaan sisältö
    if (type === 'prompt') {
        initializePromptPanel();
    }
}

function initializePromptPanel() {
    const systemPrompt = document.getElementById('system-prompt');
    const toolPrompt = document.getElementById('tool-prompt');
    
    if (!systemPrompt.textContent) {
        systemPrompt.textContent = "You are a helpful AI assistant...";
    }
    if (!toolPrompt.textContent) {
        toolPrompt.textContent = "Analyze the following request...";
    }
    
    // Tallenna promptien muutokset
    [systemPrompt, toolPrompt].forEach(prompt => {
        prompt.addEventListener('input', async () => {
            try {
                await fetch('/update_prompt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: prompt.id,
                        content: prompt.textContent
                    })
                });
            } catch (error) {
                console.error('Failed to save prompt:', error);
            }
        });
    });
}

// Estä paneelin sulkeutuminen kun klikataan sen sisältöä
document.querySelectorAll('.info-panel').forEach(panel => {
    panel.addEventListener('click', (e) => {
        e.stopPropagation();
    });
});

// Lisää word limit sliderin käsittely
function initializeWordLimitSlider() {
    const slider = document.getElementById('word-limit');
    const value = document.getElementById('word-limit-value');
    
    if (slider && value) {
        slider.addEventListener('input', async (e) => {
            const wordLimit = e.target.value;
            value.textContent = `${wordLimit} words`;
            
            try {
                const response = await fetch('/update_word_limit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ limit: wordLimit })
                });
                
                if (!response.ok) {
                    console.error('Failed to update word limit');
                }
            } catch (error) {
                console.error('Error updating word limit:', error);
            }
        });
    }
}

// Alusta kaikki kun sivu latautuu
document.addEventListener('DOMContentLoaded', () => {
    initializePromptPanel();
    initializeWordLimitSlider();  // Lisää tämä rivi
    updateTokenInfo({});  // Alusta token-näkymä
});