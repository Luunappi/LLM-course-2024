document.addEventListener('DOMContentLoaded', () => {
    // Initialize WebSocket
    const socket = io();
    
    socket.on('connect', () => {
        console.log('WebSocket connected');
    });
    
    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
    });
    
    socket.on('upload_progress', (data) => {
        updateProgressBar(data.value, data.message);
    });

    // Get DOM elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const toolButtons = document.querySelectorAll('.tool-button');
    const toolInfo = document.getElementById('tool-info');
    const micButton = document.querySelector('.btn-outline-secondary');
    const modelButton = document.querySelector('.tool-button[data-tool="model"]');
    const modelDropdown = document.getElementById('model-dropdown');

    // Initialize model dropdown
    initializeModels();

    let tokenInfoRefreshInterval = null;

    // Progress message handling
    let currentProgressMessage = null;

    // Add click handlers for tool buttons
    toolButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tool = button.dataset.tool;
            
            // Clear existing refresh interval
            if (tokenInfoRefreshInterval) {
                clearInterval(tokenInfoRefreshInterval);
                tokenInfoRefreshInterval = null;
            }
            
            // If button is already active, remove info and active state
            if (button.classList.contains('active')) {
                button.classList.remove('active');
                toolInfo.classList.remove('active');
                return;
            }
            
            // Remove active class from all buttons
            toolButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');

            // Handle the tool click
            handleToolClick(tool);
        });
    });

    // Initialize models
    async function initializeModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            
            // Get current model
            const currentModel = data.current || data.models.find(m => m.name === 'gpt-4o-mini');
            
            // Store current model name globally
            window.currentModelName = currentModel.name;
        } catch (error) {
            console.error('Error initializing models:', error);
            appendMessage('error', `Error loading models: ${error.message}`);
        }
    }
    
    function updateModelButton(model) {
        if (modelButton) {
            modelButton.textContent = model.button_name || model.name;
        }
    }

    // Handle model button click separately
    modelButton.addEventListener('click', (e) => {
        e.stopPropagation();
        modelDropdown.classList.toggle('show');
    });

    // Hide model dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!modelButton.contains(e.target) && !modelDropdown.contains(e.target)) {
            modelDropdown.classList.remove('show');
        }
    });

    // Add mic button handler
    micButton.addEventListener('click', () => {
        alert('Voice input feature coming soon!');
    });

    // Send message handler
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || sendButton.classList.contains('loading')) return;

        try {
            // Show loading state
            sendButton.classList.add('loading');
            sendButton.innerHTML = '';
            
            // Add message to chat immediately
            appendMessage('user', message);
            messageInput.value = '';

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            if (data.error) {
                appendMessage('error', `Error: ${data.error}`);
            } else if (data.response) {
                appendMessage('assistant', data.response);
            } else if (data.text) {
                appendMessage('assistant', data.text);
            } else {
                appendMessage('error', 'Received empty response from server');
            }

            // Update token info if it's currently shown
            const tokenButton = document.querySelector('.tool-button[data-tool="tokens"]');
            if (tokenButton.classList.contains('active')) {
                await showTokenInfo();
            }
        } catch (error) {
            appendMessage('error', `Error: ${error.message || 'Unknown error occurred'}`);
        } finally {
            resetSendButton();
        }
    }

    // Reset send button to normal state
    function resetSendButton() {
        sendButton.classList.remove('loading');
        sendButton.textContent = 'Send';
    }

    // Add message to chat
    function appendMessage(role, content) {
        const chatContent = document.querySelector('.chat-content');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'assistant') {
            // Convert markdown to HTML while preserving line breaks
            const formattedContent = content
                .split('\n').map(line => {
                    // Convert markdown bold to HTML strong
                    line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    return line;
                }).join('<br>');
            
            contentDiv.innerHTML = formattedContent;
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        chatContent.appendChild(messageDiv);
        chatContent.scrollTop = chatContent.scrollHeight;
    }

    // Function to update file list in Data panel
    function updateFileList(newFile = null) {
        const fileList = document.querySelector('.file-list');
        if (!fileList) return;
        
        // Get existing files
        const files = Array.from(fileList.querySelectorAll('.file-item'))
            .map(div => ({
                filename: div.querySelector('.file-name').textContent,
                is_indexed: div.querySelector('.file-status').textContent.includes('✅')
            }));
            
        // Add new file if provided
        if (newFile) {
            // Check if file already exists
            const existingIndex = files.findIndex(f => f.filename === newFile);
            if (existingIndex !== -1) {
                files[existingIndex].is_indexed = true;
            } else {
                files.push({
                    filename: newFile,
                    is_indexed: true
                });
            }
        }
        
        // Sort files by filename
        files.sort((a, b) => a.filename.localeCompare(b.filename));
        
        // Update the display
        fileList.innerHTML = '';
        files.forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'file-item';
            fileDiv.innerHTML = `
                <div class="file-name">${file.filename}</div>
                <div class="file-info">
                    <span class="file-status">
                        <i class="bi bi-file-text"></i>
                        ${file.is_indexed ? '✅ Indexed' : '❌ Not indexed'}
                    </span>
                </div>
            `;
            fileList.appendChild(fileDiv);
        });
    }

    // File upload handler
    async function handleUpload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.txt,.pdf,.doc,.docx';
        
        input.onchange = async function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            
            // Get status message element
            const statusMessage = document.getElementById('upload-status-message');
            if (statusMessage) {
                statusMessage.textContent = 'Aloitetaan tiedoston käsittelyä...';
            }
            
            try {
                const response = await fetch('/api/rag/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    if (statusMessage) {
                        statusMessage.textContent = `Upload error: ${data.error}`;
                        statusMessage.style.color = '#dc3545'; // Error color
                    }
                } else {
                    if (statusMessage) {
                        statusMessage.textContent = data.message;
                        statusMessage.style.color = '#28a745'; // Success color
                    }
                    // Update file list in Data panel with the new file
                    updateFileList(file.name);
                }
            } catch (error) {
                if (statusMessage) {
                    statusMessage.textContent = `Error uploading file: ${error.message}`;
                    statusMessage.style.color = '#dc3545'; // Error color
                }
            }
        };
        
        input.click();
    }

    // Update progress bar
    socket.on('upload_progress', function(data) {
        const progressBar = document.getElementById('upload-progress');
        const progressText = document.getElementById('upload-status');
        
        if (progressBar && progressText) {
            progressBar.style.width = (data.value * 100) + '%';
            progressText.textContent = data.message;
        }
    });

    // Token info display
    async function showTokenInfo() {
        try {
            const response = await fetch('/api/tool_info/tokens');
            const data = await response.json();
            console.log('Token stats:', data); // Debug logging

            // Format the token info
            let infoHtml = `
                <h4>Current Message</h4>
                <p>Input tokens: ${data.current.input_tokens}</p>
                <p>Output tokens: ${data.current.output_tokens}</p>
                <p>Cost: $${data.current.cost.toFixed(6)}</p>

                <h4>Total Usage</h4>
                <p>Total tokens: ${data.total.total_tokens}</p>
                <p>Total cost: $${data.total.total_cost.toFixed(6)}</p>

                <h4>Per Model Usage</h4>
            `;

            // Add per-model stats
            for (const [model, stats] of Object.entries(data.total.models)) {
                infoHtml += `
                    <div class="model-stats">
                        <p><strong>${model}</strong></p>
                        <p>Tokens: ${stats.tokens}</p>
                        <p>Cost: $${stats.cost.toFixed(6)}</p>
                    </div>
                `;
            }

            // Show the info
            const toolInfo = document.getElementById('tool-info');
            toolInfo.innerHTML = infoHtml;
            toolInfo.classList.add('active');
        } catch (error) {
            console.error('Error fetching token info:', error);
            const toolInfo = document.getElementById('tool-info');
            toolInfo.innerHTML = `<p class="error">Error loading token information: ${error.message}</p>`;
            toolInfo.classList.add('active');
        }
    }

    // System info display
    async function showSystemInfo() {
        showProgressBar('Loading system information...');
        try {
            const response = await fetch('/api/system/stats');
            const data = await response.json();
            
            toolInfo.innerHTML = `
                <div class="system-info">
                    <h3>System Information</h3>
                    <div class="timing-info">
                        <h4>Timing</h4>
                        <div class="stat-item">
                            <span class="stat-label">Total Time:</span>
                            <span class="stat-value">${data.total_time.toFixed(2)}s</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Uptime:</span>
                            <span class="stat-value">${data.additional_metrics.uptime.toFixed(2)}s</span>
                        </div>
                    </div>
                    
                    <div class="memory-info">
                        <h4>Memory Usage</h4>
                        <div class="stat-item">
                            <span class="stat-label">RSS:</span>
                            <span class="stat-value">${data.additional_metrics.memory_usage.rss.toFixed(2)} MB</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">VMS:</span>
                            <span class="stat-value">${data.additional_metrics.memory_usage.vms.toFixed(2)} MB</span>
                        </div>
                    </div>

                    <div class="components-info">
                        <h4>Active Components</h4>
                        <div class="components-list">
                            ${data.additional_metrics.active_components.map(component => `
                                <div class="component-item">${component}</div>
                            `).join('')}
                        </div>
                    </div>

                    <div class="steps-info">
                        <h4>Processing Steps</h4>
                        ${data.steps.map(step => `
                            <div class="step-item">
                                <div class="step-header">
                                    <span class="step-name">${step.step}</span>
                                    <span class="step-time">${step.time.toFixed(2)}s</span>
                                </div>
                                ${step.details ? `
                                    <div class="step-details">
                                        ${Object.entries(step.details).map(([key, value]) => `
                                            <div class="detail-item">
                                                <span class="detail-label">${key}:</span>
                                                <span class="detail-value">${value}</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            toolInfo.classList.add('active');
        } catch (error) {
            appendMessage('error', `Error loading system information: ${error.message}`);
        } finally {
            hideProgressBar();
        }
    }

    // Prompt info display
    async function showPromptInfo() {
        showProgressBar('Loading prompt information...');
        try {
            const response = await fetch('/api/prompts');
            const data = await response.json();
            
            toolInfo.innerHTML = `
                <div class="prompt-info">
                    <h3>Prompt Settings</h3>
                    
                    <div class="response-length-control">
                        <h4>Response Length</h4>
                        <div class="slider-container">
                            <input type="range" id="response-length-slider" 
                                   min="10" max="250" value="${data.response_length || 50}" 
                                   class="slider">
                            <div class="slider-value">
                                <span id="response-length-value">${data.response_length || 50}</span> words
                            </div>
                        </div>
                    </div>

                    <div class="active-prompts">
                        <h4>Active Prompts</h4>
                        ${Object.entries(data.active).map(([type, content]) => `
                            <div class="prompt-section">
                                <div class="prompt-header">
                                    <span class="prompt-type">${type}</span>
                                </div>
                                <div class="prompt-content">
                                    <textarea class="prompt-editor" data-type="${type}" data-name="active">${content}</textarea>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <div class="available-prompts">
                        <h4>Available Prompts</h4>
                        ${Object.entries(data.prompts).map(([category, prompts]) => `
                            <div class="prompt-category">
                                <h5>${category}</h5>
                                ${Object.entries(prompts).map(([name, content]) => `
                                    <div class="prompt-section">
                                        <div class="prompt-header">
                                            <span class="prompt-name">${name}</span>
                                            <button class="use-prompt-btn" data-type="${category}" data-name="${name}">Use</button>
                                        </div>
                                        <div class="prompt-content">
                                            <textarea class="prompt-editor" data-type="${category}" data-name="${name}">${content}</textarea>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            // Add event listeners for prompt editors
            document.querySelectorAll('.prompt-editor').forEach(editor => {
                editor.addEventListener('change', async () => {
                    try {
                        const response = await fetch('/api/prompts/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                type: editor.dataset.type,
                                name: editor.dataset.name,
                                content: editor.value
                            })
                        });
                        
                        const result = await response.json();
                        if (result.status === 'success') {
                            appendMessage('system', 'Prompt updated successfully');
                        } else {
                            appendMessage('error', result.error || 'Failed to update prompt');
                        }
                    } catch (error) {
                        appendMessage('error', `Error updating prompt: ${error.message}`);
                    }
                });
            });

            // Add event listeners for "Use" buttons
            document.querySelectorAll('.use-prompt-btn').forEach(button => {
                button.addEventListener('click', async () => {
                    try {
                        const promptType = button.dataset.type;
                        const promptName = button.dataset.name;
                        const content = document.querySelector(`.prompt-editor[data-type="${promptType}"][data-name="${promptName}"]`).value;
                        
                        const response = await fetch('/api/prompts/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                type: promptType,
                                name: promptName,
                                content: content
                            })
                        });
                        
                        const result = await response.json();
                        if (result.status === 'success') {
                            appendMessage('system', `Now using ${promptName} prompt for ${promptType}`);
                            showPromptInfo(); // Refresh the display
                        } else {
                            appendMessage('error', result.error || 'Failed to update prompt');
                        }
                    } catch (error) {
                        appendMessage('error', `Error updating prompt: ${error.message}`);
                    }
                });
            });

            // Add event listener for the slider
            const slider = document.getElementById('response-length-slider');
            const valueDisplay = document.getElementById('response-length-value');
            
            slider.addEventListener('input', (e) => {
                valueDisplay.textContent = e.target.value;
            });

            slider.addEventListener('change', async () => {
                try {
                    const response = await fetch('/api/prompts/length', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            response_length: parseInt(slider.value)
                        })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        appendMessage('system', `Response length set to ${slider.value} words`);
                    } else {
                        appendMessage('error', result.error || 'Failed to update response length');
                    }
                } catch (error) {
                    appendMessage('error', `Error updating response length: ${error.message}`);
                }
            });

            toolInfo.classList.add('active');
        } catch (error) {
            appendMessage('error', `Error loading prompt information: ${error.message}`);
        } finally {
            hideProgressBar();
        }
    }

    // Debug info display
    async function showDebugInfo() {
        showProgressBar('Loading debug information...');
        try {
            const response = await fetch('/api/debug/info');
            const data = await response.json();
            
            toolInfo.innerHTML = `
                <div class="debug-info">
                    <h3>Debug Information</h3>
                    <div class="debug-stats">
                        <div class="stat-item">
                            <span class="stat-label">Total Events:</span>
                            <span class="stat-value">${data.stats?.total_events || 0}</span>
                        </div>
                        <div class="stat-item error">
                            <span class="stat-label">Errors:</span>
                            <span class="stat-value">${data.stats?.error_count || 0}</span>
                        </div>
                    </div>
                </div>
            `;
            toolInfo.classList.add('active');
        } catch (error) {
            appendMessage('error', `Error loading debug information: ${error.message}`);
        } finally {
            hideProgressBar();
        }
    }

    // Progress bar functions
    function updateProgressBar(value, message) {
        if (!message) return;
        
        if (currentProgressMessage) {
            // Update existing progress message
            currentProgressMessage.querySelector('.message-content').textContent = message;
        } else {
            // Create new progress message
            const chatContent = document.querySelector('.chat-content');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = message;
            
            messageDiv.appendChild(contentDiv);
            chatContent.appendChild(messageDiv);
            
            currentProgressMessage = messageDiv;
            chatContent.scrollTop = chatContent.scrollHeight;
        }
    }

    function showProgressBar(message) {
        if (message) {
            updateProgressBar(0, message);
        }
    }

    function hideProgressBar() {
        // Clear the progress message reference
        currentProgressMessage = null;
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent default to avoid newline
            sendMessage();
        }
    });

    // Remove all previous reindex progress listeners
    socket.off('reindex_progress');

    // Add single reindex progress listener
    socket.on('reindex_progress', function(data) {
        // Update progress in the tool info panel instead of chat
        const toolInfo = document.getElementById('tool-info');
        if (data.message) {
            // For initial file status list or indexing progress
            const progressDiv = document.createElement('div');
            progressDiv.className = 'index-progress';
            
            if (data.message.includes(': Already indexed') || data.message.includes(': Not indexed')) {
                progressDiv.textContent = data.message;
            }
            else if (data.message.startsWith('Indexing ')) {
                const filename = data.message.replace('Indexing ', '').replace('...', '');
                progressDiv.textContent = `⏳ ${filename}`;
            }
            else if (data.message.includes('Completed indexing: ')) {
                const parts = data.message.split('Completed indexing: ')[1].split(' (');
                const filename = parts[0];
                const time = parts[1].replace(')', '');
                progressDiv.textContent = `✅ ${filename} - ${time}`;
            }
            
            toolInfo.appendChild(progressDiv);
            toolInfo.scrollTop = toolInfo.scrollHeight;
        }
    });

    // Function to show index information
    function showIndexInfo() {
        const toolInfo = document.getElementById('tool-info');
        
        // Clear any existing content and add the header
        toolInfo.innerHTML = `
            <div class="panel-header">
                <h3>Indexed Files</h3>
                <button id="reindex-all-button" class="action-button">
                    <i class="bi bi-arrow-clockwise"></i> Reindex All Files
                </button>
            </div>
        `;
        
        // Make the panel visible
        toolInfo.classList.add('active');
        
        // Fetch and display the file list
        fetch('/api/rag/files')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.files) {
                const fileList = document.createElement('div');
                fileList.className = 'file-list';
                
                data.files.forEach(file => {
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'file-item';
                    fileDiv.innerHTML = `
                        <div class="file-name">${file.filename}</div>
                        <div class="file-info">
                            <span class="file-status">${file.is_indexed ? '✅ Indexed' : '❌ Not indexed'}</span>
                        </div>
                    `;
                    fileList.appendChild(fileDiv);
                });
                
                toolInfo.appendChild(fileList);

                // Add click handler for reindex button
                document.getElementById('reindex-all-button').addEventListener('click', () => {
                    reindexFiles();
                });
            } else {
                toolInfo.innerHTML += '<div class="error">Failed to load index information</div>';
            }
        })
        .catch(error => {
            toolInfo.innerHTML += `<div class="error">Error loading index info: ${error.message}</div>`;
        });
    }

    // Reindex function
    function reindexFiles() {
        const toolInfo = document.getElementById('tool-info');
        toolInfo.innerHTML = `
            <div class="panel-header">
                <h3>Reindexing Files...</h3>
            </div>
        `;
        
        fetch('/api/rag/reindex', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                toolInfo.innerHTML += `<div class="error">Error: ${data.error}</div>`;
            } else {
                toolInfo.innerHTML += `<div class="success">${data.message}</div>`;
                // After reindexing, show the updated file list
                showIndexInfo();
            }
        })
        .catch(error => {
            toolInfo.innerHTML += `<div class="error">Error: ${error.message}</div>`;
        });
    }

    async function showDocumentInfo() {
        showProgressBar('Loading document information...');
        try {
            const response = await fetch('/api/rag/files');
            const data = await response.json();
            
            if (data.status === 'success' && data.files) {
                toolInfo.innerHTML = `
                    <div class="document-info">
                        <h3>Saved Documents</h3>
                        <div class="document-list">
                            ${data.files.map(file => `
                                <div class="document-item">
                                    <div class="document-header">
                                        <h4>${file.filename}</h4>
                                        <span class="document-meta">
                                            Type: ${file.type} | 
                                            Chunks: ${file.chunk_count} | 
                                            Added: ${new Date(file.timestamp * 1000).toLocaleString()}
                                        </span>
                                    </div>
                                    <div class="document-summary">
                                        <h5>Summary</h5>
                                        <p>${file.summary}</p>
                                    </div>
                                    <div class="document-samples">
                                        <h5>Sample Content</h5>
                                        ${file.sample_content.map(sample => `
                                            <div class="content-sample">
                                                <span class="chunk-id">Chunk ${sample.chunk_id}</span>
                                                <p>${sample.content}</p>
                                            </div>
                                        `).join('')}
                                    </div>
                                    <div class="document-actions">
                                        <button onclick="reindexDocument('${file.filename}')" class="action-button">
                                            <i class="fas fa-sync"></i> Reindex
                                        </button>
                                        <button onclick="deleteDocument('${file.filename}')" class="action-button delete">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                toolInfo.innerHTML = `
                    <div class="document-info">
                        <h3>Saved Documents</h3>
                        <p>No documents found</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading document info:', error);
            toolInfo.innerHTML = `
                <div class="document-info">
                    <h3>Saved Documents</h3>
                    <p class="error">Error loading document information</p>
                </div>
            `;
        }
        hideProgressBar();
    }

    async function reindexDocument(filename) {
        showProgressBar('Reindexing document...');
        try {
            const response = await fetch('/api/rag/reindex', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                appendMessage('system', `Successfully reindexed ${filename}`);
                showDocumentInfo(); // Refresh the document list
            } else {
                appendMessage('error', result.error || 'Failed to reindex document');
            }
        } catch (error) {
            appendMessage('error', `Error reindexing document: ${error.message}`);
        }
        hideProgressBar();
    }

    async function deleteDocument(filename) {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) {
            return;
        }
        
        showProgressBar('Deleting document...');
        try {
            const response = await fetch('/api/rag/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                appendMessage('system', `Successfully deleted ${filename}`);
                showDocumentInfo(); // Refresh the document list
            } else {
                appendMessage('error', result.error || 'Failed to delete document');
            }
        } catch (error) {
            appendMessage('error', `Error deleting document: ${error.message}`);
        }
        hideProgressBar();
    }

    // Add event listener for the document info button
    document.querySelector('.tool-button[data-tool="documents"]').addEventListener('click', () => {
        showDocumentInfo();
    });

    // Generic function to show tool panel
    function showToolPanel(title, content) {
        const toolInfo = document.getElementById('tool-info');
        
        // Clear and set up the panel
        toolInfo.innerHTML = `
            <div class="panel-header">
                <h3>${title}</h3>
                ${content.headerButtons || ''}
            </div>
            <div class="panel-content">
                ${content.body || ''}
            </div>
        `;
        
        // Make the panel visible
        toolInfo.classList.add('active');
        
        // Execute any callback if provided
        if (content.callback) {
            content.callback(toolInfo);
        }
    }

    // Handle different tools using the generic panel
    function handleToolClick(tool) {
        switch(tool) {
            case 'upload':
                showToolPanel('Upload Document', {
                    body: `
                        <div class="upload-area" id="upload-area">
                            <div class="upload-instructions">
                                <p>Drag and drop a file here or click to select</p>
                                <p class="upload-formats">Supported formats: PDF, TXT</p>
                            </div>
                        </div>
                        <div id="upload-status-message" class="status-message"></div>
                    `,
                    callback: (panel) => {
                        const uploadArea = panel.querySelector('#upload-area');
                        uploadArea.addEventListener('click', () => {
                            handleUpload();
                        });
                    }
                });
                break;

            case 'model':
                showToolPanel('Model Selection', {
                    body: `
                        <div class="model-settings">
                            <div class="model-option ${window.currentModelName === 'gpt-4o' ? 'selected' : ''}" data-model="gpt-4o">
                                <h4>GPT-4o</h4>
                                <p>Most capable model, best for complex tasks and reasoning</p>
                            </div>
                            <div class="model-option ${window.currentModelName === 'gpt-4o-mini' ? 'selected' : ''}" data-model="gpt-4o-mini">
                                <h4>GPT-4o Mini</h4>
                                <p>Balanced performance and speed, good for most tasks</p>
                            </div>
                            <div class="model-option ${window.currentModelName === 'o1-mini' ? 'selected' : ''}" data-model="o1-mini">
                                <h4>O1 Mini</h4>
                                <p>Fastest model, best for simple tasks and quick responses</p>
                            </div>
                        </div>
                    `,
                    callback: (panel) => {
                        // Add click handlers for model selection
                        panel.querySelectorAll('.model-option').forEach(option => {
                            option.addEventListener('click', async () => {
                                const modelName = option.dataset.model;
                                try {
                                    showProgressBar('Switching model...');
                                    const response = await fetch('/api/models/select', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json',
                                        },
                                        body: JSON.stringify({ model: modelName })
                                    });
                                    
                                    const result = await response.json();
                                    if (result.status === 'success') {
                                        // Update selected model
                                        window.currentModelName = modelName;
                                        panel.querySelectorAll('.model-option').forEach(opt => {
                                            opt.classList.toggle('selected', opt.dataset.model === modelName);
                                        });
                                        appendMessage('system', `Model changed to ${modelName}`);
                                    } else {
                                        appendMessage('error', result.error || 'Failed to change model');
                                    }
                                } catch (error) {
                                    appendMessage('error', `Error changing model: ${error.message}`);
                                } finally {
                                    hideProgressBar();
                                }
                            });
                        });
                    }
                });
                break;

            case 'tokens':
                showToolPanel('Token Usage', {
                    body: `
                        <div class="token-info">
                            <div class="token-stats">
                                <h4>Current Session</h4>
                                <div id="token-count">Loading...</div>
                                <div id="token-cost">Calculating...</div>
                            </div>
                            <div class="token-history">
                                <h4>Usage History</h4>
                                <div id="token-chart"></div>
                            </div>
                        </div>
                    `,
                    callback: (panel) => {
                        updateTokenInfo();
                        // Start auto-refresh for token info
                        tokenInfoRefreshInterval = setInterval(updateTokenInfo, 5000);
                    }
                });
                break;

            case 'system':
                showToolPanel('System Information', {
                    body: `
                        <div class="system-info">
                            <div class="info-section">
                                <h4>System Status</h4>
                                <p>API Status: <span class="status-badge connected">Connected</span></p>
                                <p>Current Model: <span id="current-model">Loading...</span></p>
                                <p>Memory Usage: <span id="memory-usage">Loading...</span></p>
                            </div>
                            <div class="info-section">
                                <h4>Performance</h4>
                                <p>Average Response Time: <span id="avg-response-time">Loading...</span></p>
                                <p>Requests/min: <span id="requests-per-min">Loading...</span></p>
                            </div>
                        </div>
                    `,
                    callback: (panel) => {
                        updateSystemInfo();
                    }
                });
                break;

            case 'prompt':
                showToolPanel('Prompt Settings', {
                    body: `
                        <div class="prompt-settings">
                            <div class="prompt-section">
                                <h4>System Prompt</h4>
                                <div id="system-prompt" class="prompt-text" contenteditable="true"></div>
                            </div>
                            <div class="prompt-section">
                                <h4>Response Settings</h4>
                                <div class="setting-group">
                                    <label>Response Length</label>
                                    <div class="word-limit-control">
                                        <input type="range" id="word-limit" min="10" max="250" value="50" step="10">
                                        <span id="word-limit-value">50 words</span>
                                    </div>
                                </div>
                                <div class="setting-group">
                                    <label>Temperature</label>
                                    <div class="temperature-control">
                                        <input type="range" id="temperature" min="0" max="100" value="70" step="10">
                                        <span id="temperature-value">0.7</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `,
                    callback: (panel) => {
                        setupPromptHandlers();
                    }
                });
                break;

            case 'index-data':
                showToolPanel('Files', {
                    headerButtons: `
                        <button id="reindex-all-button" class="action-button">
                            <i class="bi bi-arrow-clockwise"></i> Reindex All Files
                        </button>
                    `,
                    body: '<div class="file-list"></div>',
                    callback: async (panel) => {
                        const fileList = panel.querySelector('.file-list');
                        if (!fileList) return;
                        
                        // Kovakoodatut tiedostot
                        const files = [
                            { filename: "Essee - Eettinen ja moraalinen seuranta älykkäissä moniagenttiohjelmissa.pdf", is_indexed: true },
                            { filename: "Essee - Tekoälyavustajan ihmisyyden rajat ja orjan dilemma.pdf", is_indexed: true },
                            { filename: "Digi perusteet.pdf", is_indexed: true },
                            { filename: "Meta-prompting.pdf", is_indexed: true },
                            { filename: "Caroline Bassett - Anti-computing_ Dissent And The Machine-Manchester University Press (2021).pdf", is_indexed: true },
                            { filename: "Gradu suomi v5.6.pdf", is_indexed: true },
                            { filename: "toimeenpanosuunnitelma_farmasia.pdf", is_indexed: true },
                            { filename: "toimeenpanosuunnitelma_humanistinen.pdf", is_indexed: true },
                            { filename: "toimeenpanosuunnitelma_matlu.pdf", is_indexed: true },
                            { filename: "tsla-20231231-gen.pdf", is_indexed: true }
                        ];
                        
                        fileList.innerHTML = ''; // Clear existing content
                        
                        files.forEach(file => {
                            const fileDiv = document.createElement('div');
                            fileDiv.className = 'file-item';
                            fileDiv.innerHTML = `
                                <div class="file-name">${file.filename}</div>
                                <div class="file-info">
                                    <span class="file-status">
                                        <i class="bi bi-file-text"></i>
                                        ${file.is_indexed ? '✅ Indexed' : '❌ Not indexed'}
                                    </span>
                                </div>
                            `;
                            fileList.appendChild(fileDiv);
                        });
                        
                        // Add click handler for reindex button
                        const reindexButton = document.getElementById('reindex-all-button');
                        if (reindexButton) {
                            reindexButton.addEventListener('click', reindexFiles);
                        }
                    }
                });
                break;
        }
    }
});