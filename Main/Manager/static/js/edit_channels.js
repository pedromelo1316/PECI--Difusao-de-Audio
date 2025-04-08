let streamingSources = [];
function updateSectionRight(value) {
    const sectionRight = document.getElementById("sectionRightContent");
    const saveButtonContainer = document.getElementById("saveButtonContainer");

    // Reset classes and display
    sectionRight.className = "inner-dual-section";
    sectionRight.style.display = 'flex';

    if (value === "local") {
        let playlistsHTML = '';
        for (const [playlistName, songs] of Object.entries(playlistsData)) {
            playlistsHTML += `
                <div class="playlist-item" style="display: flex; flex-direction: column; border: 1px solid #ccc; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <button class="toggle-songs-btn" onclick="toggleSongsVisibility(this)" style="background: none; border: none; cursor: pointer; margin-right: 10px;">
                            <i class="fa-solid fa-chevron-down"></i>
                        </button>
                        <label for="playlist-${playlistName}" style="flex-grow: 1;">
                            <span class="playlist-name">${playlistName}</span>
                        </label>
                        <input type="checkbox" id="playlist-${playlistName}" onchange="addToPlaylist('${playlistName}', 'playlist', this.checked)">
                    </div>
                    <div class="songs-list" style="display: none; padding-left: 20px; margin-top: 5px;">
                        ${songs.map(song => `
                            <div class="song-item" style="display: flex; justify-content: space-between; align-items: center;">
                                <span>${song}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    
        let songsHTML = '';
        allSongs.forEach(song => {
            songsHTML += `
                <div class="song-item" style="display: flex; justify-content: space-between; align-items: center;">
                    <label for="song-${song}" style="flex-grow: 1;">
                        <span class="song-name">${song}</span>
                    </label>
                    <input type="checkbox" id="song-${song}" onchange="addToPlaylist('${song}', 'song', this.checked)">
                </div>
            `;
        });
    
        sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h3>Lista de reprodução</h3>
                <div class="selected-playlist-info">
                    <div class="playlist-dropzone"></div>
                </div>
            </div>
            <div class="inner-section-right">
                <h3>Playlists Disponíveis</h3>
                <div class="playlist-container">
                    ${playlistsHTML}
                </div>
                <h3>Músicas Disponíveis</h3>
                <div class="songs-container">
                    ${songsHTML}
                </div>
            </div>
        `;
        saveButtonContainer.style.display = "flex";
        enablePlaylistReordering(); // Enable drag-and-drop reordering
    
    } else if (value === "streaming") {
        let streamingHTML = '';
        streamingSources2.forEach(source => {
            streamingHTML += `
                <div class="streaming-item" style="display: flex; justify-content: space-between; align-items: center; border: 1px solid #ccc; margin-bottom: 10px; padding: 5px;">
                    <label for="streaming-${source}" style="flex-grow: 1;">
                        <span class="streaming-">${source}</span>
                    </label>
                    <input type="radio" name="streaming-source" id="streaming-${source}" onchange="selectStreamingSource('${source}')">
                </div>
            `;
        });
    
        sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h3 id="Streaming_Source_Message">Fonte de Streaming:</h3>
                <div class="selected-streaming-info">
                    <p class="section-hint">Selecione uma fonte de streaming</p>
                    <div id="selectedStreamingDisplay" style="margin-top: 10px; font-weight: bold;"></div>
                </div>
            </div>
            <div class="inner-section-right">
                <h3>Fontes Disponíveis</h3>
                <div class="streaming-container">
                    ${streamingHTML}
                </div>
            </div>
        `;
        saveButtonContainer.style.display = "flex";
    } else {
        sectionRight.className = "inner-dual-section empty-message";
        sectionRight.innerHTML = `<p style="text-align:center;">Selecione o tipo de reprodução que pretende</p>`;
        saveButtonContainer.style.display = "none";
    }
}

function selectStreamingSource(source) {
    const selectedDisplay = document.getElementById("selectedStreamingDisplay");
    const hintMessage = document.querySelector(".section-hint");

    // Oculta a mensagem de dica
    if (hintMessage) {
        hintMessage.style.display = "none";
    }

    // Atualiza a exibição da fonte selecionada com um novo estilo
    selectedDisplay.innerHTML = `
        <div class="streaming-selected-box">
            <span class="streaming-label">Fonte Selecionada:</span>
            <span class="streaming-name-selected">${source}</span>
        </div>
    `;
}


function toggleSongsVisibility(button) {
    const songsList = button.parentElement.nextElementSibling; // A lista de músicas está logo após o cabeçalho
    const isVisible = songsList.style.display === 'block';

    // Alterna a visibilidade
    songsList.style.display = isVisible ? 'none' : 'block';

    // Alterna o ícone da seta
    const icon = button.querySelector('i');
    icon.classList.toggle('fa-chevron-down', !isVisible);
    icon.classList.toggle('fa-chevron-up', isVisible);
}

function addToPlaylist(itemName, itemType, isChecked) {
    const dropZone = document.querySelector('.playlist-dropzone');

    if (isChecked) {
        // Avoid duplicates
        const existingItems = Array.from(dropZone.querySelectorAll('.playlist-item, .song-item'));
        const isDuplicate = existingItems.some(item => item.dataset.name === itemName);

        if (!isDuplicate) {
            const newItem = document.createElement('div');
            newItem.className = itemType === 'playlist' ? 'playlist-item' : 'song-item';
            newItem.dataset.name = itemName;
            newItem.innerHTML = `
                <span>${itemName}</span>
                <button class="remove-item-btn" onclick="removeItemFromPlaylist(this)">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            `;
            dropZone.appendChild(newItem);
            enablePlaylistReordering(); // Re-enable drag-and-drop for the new item
        }
    } else {
        // Remove the item if unchecked
        const itemToRemove = dropZone.querySelector(`[data-name="${itemName}"]`);
        if (itemToRemove) {
            itemToRemove.remove();
        }
    }
}

function enablePlaylistReordering() {
    const dropZone = document.querySelector('.playlist-dropzone');
    const items = dropZone.querySelectorAll('.playlist-item, .song-item');

    items.forEach(item => {
        item.setAttribute('draggable', true);

        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', item.dataset.name);
            item.classList.add('dragging');
        });

        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
        });
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        const draggingItem = document.querySelector('.dragging');
        const afterElement = getDragAfterElement(dropZone, e.clientY);
        if (afterElement == null) {
            dropZone.appendChild(draggingItem);
        } else {
            dropZone.insertBefore(draggingItem, afterElement);
        }
    });
}

function removeItemFromPlaylist(button) {
    const item = button.parentElement; // O botão está dentro do item a ser removido
    const dropZone = document.querySelector('.playlist-dropzone');

    if (dropZone.contains(item)) {
        const itemName = item.dataset.name; // Obtém o nome do item
        const checkbox = document.getElementById(`playlist-${itemName}`) || document.getElementById(`song-${itemName}`);
        
        if (checkbox) {
            checkbox.checked = false; // Desmarca o checkbox correspondente
        }

        item.remove(); // Remove o item da lista de reprodução
    }
}
function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.playlist-item:not(.dragging), .song-item:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function removeStreamingSource(source) {
    const index = streamingSources.indexOf(source);
    if (index > -1) {
        streamingSources.splice(index, 1);
        updateSectionRight('streaming'); // Refresh the streaming section
    }
}

function openAddStreamingModal() {
    const newSource = prompt("Digite o nome da nova fonte de streaming:");
    if (newSource) {
        streamingSources.push(newSource);
        updateSectionRight('streaming'); // Refresh the streaming section
    }
}

function associateMicrophone(deviceId, label) {
    const associatedMicrophones = document.getElementById("associatedMicrophones");
    const microphoneItem = document.createElement("div");
    microphoneItem.className = "microphone-item";
    microphoneItem.innerHTML = `
        <span>${label || "Microfone Desconhecido"}</span>
        <button class="remove-item-btn" onclick="removeMicrophone(this)">
            <i class="fa-solid fa-trash-can"></i>
        </button>
    `;
    associatedMicrophones.appendChild(microphoneItem);
}

function removeMicrophone(button) {
    const microphoneItem = button.parentElement;
    microphoneItem.remove();
}

// Change event listeners from radio buttons to menu items
document.addEventListener('DOMContentLoaded', function() {
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            menuItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Update content based on selected menu item
            const value = this.getAttribute('data-value');
            updateSectionRight(value);
        });
    });
    
    // Set default selected item (Local)
    const defaultItem = document.querySelector('.menu-item[data-value="local"]');
    if (defaultItem) {
        defaultItem.classList.add('active');
        updateSectionRight(defaultItem.getAttribute('data-value'));
    }
    enableDragAndDrop();
    updateLeftStats();
});

function loadMicrophones() {
    fetch('/get_microphones')
        .then(response => response.json())
        .then(microphones => {
            const microphoneSelect = document.getElementById('microphoneSelect');
            microphoneSelect.innerHTML = '<option value="">Select a microphone</option>'; // Reset options

            microphones.forEach(mic => {
                const option = document.createElement('option');
                option.value = `${mic.card}:${mic.device}`;
                option.textContent = mic.name || `Card ${mic.card}, Device ${mic.device}`;
                microphoneSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching microphones:', error);
        });
}

function saveChanges() {
    // Obtém o tipo de transmissão selecionado no menu-list
    const selectedMenuItem = document.querySelector('.menu-item.active');
    const transmissionType = selectedMenuItem ? selectedMenuItem.getAttribute('data-value') : null;

    // Obtém a lista de reprodução ou o streaming selecionado em section-rightCH
    let selectedSource = null;
    if (transmissionType === "local") {
        const selectedPlaylist = document.querySelector('.playlist-container input[type="checkbox"]:checked');
        selectedSource = selectedPlaylist ? selectedPlaylist.id.replace('playlist-', '') : null;
    } else if (transmissionType === "streaming") {
        const selectedStreaming = document.querySelector('.streaming-container input[type="radio"]:checked');
        selectedSource = selectedStreaming ? selectedStreaming.id.replace('streaming-', '') : null;
    }

    // Obtém o microfone selecionado
    const microphoneSelect = document.getElementById("microphoneSelect");
    const selectedMicrophone = microphoneSelect ? microphoneSelect.value : null;

    // Verifica se todos os dados necessários foram preenchidos
    if (!transmissionType) {
        alert("Por favor, selecione o tipo de transmissão.");
        return;
    }
    if (!selectedSource) {
        alert("Por favor, selecione uma lista de reprodução ou uma fonte de streaming.");
        return;
    }
    if (!selectedMicrophone) {
        alert("Por favor, selecione um microfone.");
        return;
    }

    // Dados a serem enviados para o backend
    const data = {
        channel_type: transmissionType,
        channel_reproduction: selectedSource,
        channel_microfone: selectedMicrophone
    };

    // Envia os dados para o backend usando fetch
    fetch('/save_channel_configs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            alert("Configurações salvas com sucesso!");
        } else {
            alert("Erro ao salvar as configurações.");
        }
    })
    .catch(error => {
        console.error("Erro ao salvar as configurações:", error);
        alert("Erro ao salvar as configurações.");
    });
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', loadMicrophones);