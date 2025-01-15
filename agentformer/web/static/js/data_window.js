// Päivitä tiedostolista
function updateFileList(data) {
    const fileList = document.getElementById('indexed-files');
    fileList.innerHTML = ''; // Tyhjennä lista
    
    // Tarkista onko data ja files olemassa
    if (!data || !data.files) {
        const emptyMessage = document.createElement('li');
        emptyMessage.className = 'empty-message';
        emptyMessage.textContent = data?.message || 'Ei indeksoituja tiedostoja';
        fileList.appendChild(emptyMessage);
        return;
    }

    // Lisää tiedostot listaan
    data.files.forEach(file => {
        const li = document.createElement('li');
        li.className = 'file-item';
        li.innerHTML = `
            <span class="file-name">${file.filename}</span>
            <span class="file-status">${file.is_indexed ? '✅ Indexed' : ''}</span>
        `;
        fileList.appendChild(li);
    });
}

// Hae tiedostolista kun ikkuna avataan
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/rag/files')
        .then(response => response.json())
        .then(data => {
            updateFileList(data);
            if (data.status === 'error') {
                showMessage(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Virhe tiedostojen haussa', 'error');
        });
});

// Reindeksoi kaikki tiedostot
document.getElementById('reindex-button').addEventListener('click', function() {
    // Ensin pyydä varmistus
    fetch('/api/rag/reindex', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ confirmed: false })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'confirm') {
            if (confirm(data.message)) {
                // Käyttäjä vahvisti, suorita reindeksointi
                fetch('/api/rag/reindex', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ confirmed: true })
                })
                .then(response => response.json())
                .then(result => {
                    showMessage(result.message, result.status);
                    if (result.status === 'success') {
                        updateFileList(result.indexed_files || []);
                    }
                });
            }
        } else {
            showMessage(data.message, data.status);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Reindeksointi epäonnistui', 'error');
    });
});

// Päivitä indeksi (indeksoi vain puuttuvat)
document.getElementById('update-index-button').addEventListener('click', function() {
    fetch('/api/rag/update_index', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        showMessage(data.message, data.status);
        if (data.status === 'success') {
            updateFileList(data.indexed_files || []);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Indeksin päivitys epäonnistui', 'error');
    });
});

// Tiedoston lataus (indeksoidaan automaattisesti)
document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    showMessage('Ladataan tiedostoa...', 'info');
    
    fetch('/api/rag/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showMessage(data.message, data.status);
        if (data.status === 'success') {
            updateFileList(data.indexed_files || []);
            this.reset();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Tiedoston lataus epäonnistui', 'error');
    });
});

// Apufunktio viestien näyttämiseen
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    setTimeout(() => {
        messageDiv.textContent = '';
        messageDiv.className = 'message';
    }, 5000);
}

function showError(error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    
    // Näytä yksityiskohtainen virheviesti
    if (error.error_type === 'indexing_error') {
        errorDiv.innerHTML = `
            <h4>Indeksointivirhe</h4>
            <p>${error.message}</p>
            <div class="error-details">
                <small>Tiedosto: ${error.metadata?.filename || 'tuntematon'}</small>
            </div>
        `;
    } else {
        errorDiv.textContent = error.message;
    }
    
    document.getElementById('message-container').appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Indeksoinnin keskeytys
document.getElementById('cancel-indexing').addEventListener('click', function() {
    if (confirm('Haluatko varmasti keskeyttää indeksoinnin?')) {
        fetch('/api/rag/cancel', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            showMessage(data.message, data.status);
            if (data.status === 'success') {
                document.querySelector('.progress-container').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Keskeytys epäonnistui', 'error');
        });
    }
});

// Edistymispalkin päivitys WebSocket-viesteistä
socket.on('reindex_progress', function(data) {
    const progressContainer = document.querySelector('.progress-container');
    const progressBar = document.querySelector('.progress');
    const progressText = document.querySelector('.progress-text');
    const cancelButton = document.getElementById('cancel-indexing');
    
    progressContainer.style.display = 'block';
    progressBar.style.width = `${data.value * 100}%`;
    progressText.textContent = `${Math.round(data.value * 100)}% - ${data.message}`;
    
    // Näytä/piilota keskeytysnappi
    cancelButton.style.display = data.can_cancel ? 'block' : 'none';
    
    if (data.value >= 1) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 2000);
    }
}); 