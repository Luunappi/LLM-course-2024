document.addEventListener('DOMContentLoaded', async function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        // Käytetään innerHTML:ia ja korvataan rivinvaihdot <br>-tageilla
        const htmlMessage = message.replace(/\n/g, '<br>');
        messageDiv.innerHTML = htmlMessage;

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
        const sessionStats = document.getElementById('session-stats');
        
        if (!tokenCount || !tokenCost) return;
        
        try {
            // Hae session kokonaistilastot
            const sessionResponse = await fetch('/token_info');
            const sessionData = await sessionResponse.json();
            
            // Päivitä nykyisen viestin token-käyttö
            if (data.token_usage) {
                const {input_tokens = 0, output_tokens = 0, total_tokens = 0, cost = 0} = data.token_usage;
                tokenCount.textContent = `${total_tokens} tokens used (${input_tokens} in, ${output_tokens} out)`;
                tokenCost.textContent = `Cost: $${cost.toFixed(4)}`;
            }
            
            // Päivitä session kokonaistilastot
            let sessionStatsHtml = '<div class="session-totals">';
            sessionStatsHtml += `<p>Session total: ${sessionData.total_tokens} tokens ($${sessionData.total_cost.toFixed(4)})</p>`;
            sessionStatsHtml += '<p>Per model:</p><ul>';
            
            // Lisää mallikohtaiset tilastot
            for (const [model, stats] of Object.entries(sessionData.models)) {
                sessionStatsHtml += `<li>${model}: ${stats.tokens} tokens ($${stats.cost.toFixed(4)})</li>`;
            }
            sessionStatsHtml += '</ul></div>';
            
            sessionStats.innerHTML = sessionStatsHtml;
        } catch (error) {
            console.error('Error updating token info:', error);
        }
    }

    // Model selector handling
    const modelBtn = document.getElementById('model-select-btn');
    const modelDropdown = document.getElementById('model-dropdown');
    
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

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        if (modelDropdown) {
            modelDropdown.style.display = 'none';
        }
    });

    // Alusta mallinvalitsin heti kun sivu on latautunut
    await initializeModelSelector();
});

async function initializeModelSelector() {
    try {
        const modelNameElement = document.querySelector('.model-name');
        if (!modelNameElement) {
            console.error('Model name element not found');
            return;
        }

        // Hae nykyinen malli
        const currentResponse = await fetch('/models/current');
        if (!currentResponse.ok) {
            throw new Error(`HTTP error! status: ${currentResponse.status}`);
        }
        const currentModel = await currentResponse.json();
        console.log('Current model data:', currentModel);

        // Tarkista että data sisältää tarvittavat kentät
        if (!currentModel || !currentModel.button_name) {
            console.error('Invalid model data received:', currentModel);
            modelNameElement.textContent = 'gpt-4o-mini';
            return;
        }
        
        // Aseta nykyisen mallin nimi nappiin
        modelNameElement.textContent = currentModel.button_name;
        
        // Hae saatavilla olevat mallit
        const availableResponse = await fetch('/models/available');
        if (!availableResponse.ok) {
            throw new Error(`HTTP error! status: ${availableResponse.status}`);
        }
        const availableModels = await availableResponse.json();
        console.log('Available models:', availableModels);
        
        const modelDropdown = document.getElementById('model-dropdown');
        if (!modelDropdown) {
            console.error('Model dropdown element not found');
            return;
        }

        modelDropdown.innerHTML = '';
        
        // Lisää mallit dropdowniin
        if (Array.isArray(availableModels)) {
            availableModels.forEach(model => {
                if (!model || !model.name || !model.button_name || !model.display_name) {
                    console.error('Invalid model data:', model);
                    return;
                }
                const option = document.createElement('div');
                option.className = 'model-option';
                option.dataset.model = model.name;
                option.dataset.buttonName = model.button_name;
                option.dataset.displayName = model.display_name;
                option.textContent = model.display_name;
                modelDropdown.appendChild(option);

                // Lisää click handler jokaiselle vaihtoehdolle
                option.addEventListener('click', async () => {
                    const selectedModel = option.dataset.model;
                    const buttonName = option.dataset.buttonName;
                    
                    try {
                        const response = await fetch('/switch_model', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ model: selectedModel })
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        const data = await response.json();
                        console.log('Switch model response:', data); // Debug-loggaus
                        
                        if (data.success) {
                            // Käytä palautetun mallin tietoja
                            const model = data.model;
                            if (model && model.button_name) {
                                modelNameElement.textContent = model.button_name;
                            } else {
                                // Fallback jos palvelin ei palauta mallin tietoja
                                modelNameElement.textContent = buttonName;
                            }
                            modelDropdown.style.display = 'none';
                            await updateTokenInfo({});
                        } else {
                            console.error('Failed to switch model:', data.error);
                        }
                    } catch (error) {
                        console.error('Error switching model:', error);
                    }
                });
            });
        } else {
            console.error('Available models is not an array:', availableModels);
        }
    } catch (error) {
        console.error('Error initializing model selector:', error);
        const modelNameElement = document.querySelector('.model-name');
        if (modelNameElement) {
            modelNameElement.textContent = 'gpt-4o-mini';
        }
    }
}

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