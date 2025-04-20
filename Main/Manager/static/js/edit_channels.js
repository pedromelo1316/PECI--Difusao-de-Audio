let streamingSources = [];
let channelName = ""; // Variable to store channel name

function updateSectionRight(value) {
    const sectionRight = document.getElementById("sectionRightContent");
    const saveButtonContainer = document.getElementById("saveButtonContainer");

    // Reset classes and display
    sectionRight.className = "inner-dual-section";
    sectionRight.style.display = 'flex';

    if (value === "LOCAL") {
        let playlistsHTML = '';
        if (Object.keys(playlistsData).length > 0) {
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
        }

        let songsHTML = '';
        if (allSongs.length > 0) {
            allSongs.forEach(song => {
                const isChecked = associatedSongs.includes(song); // Verifica se a música está associada
                songsHTML += `
                    <div class="song-item" style="display: flex; justify-content: space-between; align-items: center;">
                        <label for="song-${song}" style="flex-grow: 1;">
                            <span class="song-name">${song}</span>
                        </label>
                        <input type="checkbox" id="song-${song}" onchange="addToPlaylist('${song}', 'song', this.checked)" ${isChecked ? 'checked' : ''}>
                    </div>
                `;
            });
        }

        // Adiciona as músicas associadas ao canal na dropzone
        let associatedSongsHTML = '';
        if (associatedSongs.length > 0) {
            associatedSongs.forEach(song => {
                associatedSongsHTML += `
                    <div class="song-item" data-name="${song}" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>${song}</span>
                        <button class="remove-item-btn" onclick="removeItemFromPlaylist(this)">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                `;
            });
        } else {
            associatedSongsHTML = `<p class="no-songs-message">No songs associated with the channel.</p>`;
        }
        if (allSongs.length === 0) {
            sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h3>${channelName} Playlist</h3>
                <div class="selected-playlist-info">
                <div class="playlist-dropzone">
                    ${associatedSongsHTML} <!-- Associated songs -->
                </div>
                </div>
            </div>
            <div class="inner-section-right">
                <div class="no-songs-warning" style="text-align: center; padding: 20px;">
                <p>No songs available. Please add media to proceed.</p>
                <button style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" class="add-media-btn" onclick="window.location.href='/secundaria'">Add Songs</button>
                </div>
            </div>
            `;
        } else {
            sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h3>${channelName} Playlist</h3>
                <div class="selected-playlist-info">
                <div class="playlist-dropzone">
                    ${associatedSongsHTML} <!-- Associated songs -->
                </div>
                </div>
            </div>
            <div class="inner-section-right">
                <div class="playlists-section">
                <span class="container-count">${Object.keys(playlistsData).length}</span>
                <h3>Available Playlists</h3>
                <div class="playlist-container">
                    ${playlistsHTML}
                </div>
                </div>
                <div class="songs-section">
                <span class="container-count">${allSongs.length}</span>
                <h3>Available Songs</h3>
                <div class="songs-container">
                    ${songsHTML}
                </div>
                </div>
            </div>
            `;
            saveButtonContainer.style.display = "flex";
            enablePlaylistReordering(); // Enable drag-and-drop reordering
        }
    
    } else if (value === "STREAMING") {
        let streamingHTML = '';
        
        if (streamingSources2.length > 0) {
            streamingSources2.forEach(source => {
                const isChecked = associatedStreaming === source;
                streamingHTML += `
                    <div class="streaming-item">
                        <label for="streaming-${source}" style="flex-grow: 1;">
                            <span class="streaming-name">${source}</span>
                        </label>
                        <input type="checkbox" id="streaming-${source}" onchange="selectStreamingSource('${source}', this)" ${isChecked ? 'checked' : ''}>
                    </div>
                `;
            });
        } else {
            streamingHTML = `
                <div class="no-streaming-warning" style="text-align: center; padding: 20px;">
                    <p>No streaming sources available.</p>
                    <button style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" class="add-streams-btn" onclick="window.location.href='/secundaria'">Add Streaming</button>
                </div>
            `;
        }

        sectionRight.innerHTML = `
            <div class="inner-section-right streaming-section">
                <span class="container-count">${streamingSources2.length}</span>
                <h3>Available Streaming Sources</h3>
                <div class="streaming-container" style="max-height: 560px; overflow-y: auto;">
                    ${streamingHTML}
                </div>
            </div>
        `;
        saveButtonContainer.style.display = "flex";
    } else {
        sectionRight.className = "inner-dual-section empty-message";
        sectionRight.innerHTML = `<p style="text-align:center;">Select the type of playback you want</p>`;
        saveButtonContainer.style.display = "none";
    }
}

function selectStreamingSource(source, checkbox) {
    // Ensure only one checkbox is selected at a time
    const allCheckboxes = document.querySelectorAll('.streaming-container input[type="checkbox"]');
    allCheckboxes.forEach(cb => {
        if (cb !== checkbox) {
            cb.checked = false;
        }
    });

    associatedStreaming = checkbox.checked ? source : null; // Update the selected streaming source
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
    const noSongsMessage = dropZone.querySelector('.no-songs-message');

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

            // Remove the "no songs" message if it exists
            if (noSongsMessage) {
                noSongsMessage.remove();
            }
        }
    } else {
        // Remove the item if unchecked
        const itemToRemove = dropZone.querySelector(`[data-name="${itemName}"]`);
        if (itemToRemove) {
            itemToRemove.remove();
			// Check if dropZone is empty and add the message back
			if (dropZone.children.length === 0) {
				dropZone.innerHTML = `<p class="no-songs-message">No songs associated with the channel.</p>`;
			}
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
    const item = button.parentElement;
    const dropZone = document.querySelector('.playlist-dropzone');

    if (dropZone.contains(item)) {
        const itemName = item.dataset.name;
        const checkbox = document.getElementById(`playlist-${itemName}`) || document.getElementById(`song-${itemName}`);
        if (checkbox) {
            checkbox.checked = false; // Desmarcar o checkbox correspondente
        }

        item.remove(); // Remove o item da dropzone

        // Se ficar vazia, mostra novamente a mensagem de "no songs"
        const remaining = dropZone.querySelectorAll('.playlist-item, .song-item').length;
        if (remaining === 0) {
            dropZone.innerHTML = `<p class="no-songs-message">No songs associated with the channel.</p>`;
        }
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
    console.log("Removing streaming source:", source);

    // Update the HTML to reset the state
    const sectionRight = document.getElementById("sectionRightContent");

    sectionRight.innerHTML = `
        <div class="inner-section-right streaming-section">
            <h3>Available Streaming Sources</h3>
            <div class="streaming-container">
                ${streamingSources2.map(src => `
                    <div class="streaming-item">
                        <label for="streaming-${src}" style="flex-grow: 1;">
                            <span>${src}</span>
                        </label>
                        <input type="checkbox" id="streaming-${src}" onchange="toggleStreamingSource('${src}', this.checked)">
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function openAddStreamingModal() {
    const newSource = prompt("Enter the name of the new streaming source:");
    if (newSource) {
        streamingSources.push(newSource);
        updateSectionRight('STREAMING'); // Refresh the streaming section
    }
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
    
    console.log("Channel type:", channelType);

    // Get channel name from the HTML
    channelName = document.getElementById("channelTitle").textContent.trim();
    
    // Set default selected item
    const defaultItem = document.querySelector('.menu-item[data-value="' + channelType + '"]');
    if (defaultItem) {
        defaultItem.classList.add('active');
        updateSectionRight(defaultItem.getAttribute('data-value'));
    }
    enableDragAndDrop();
    updateLeftStats();
});

function saveChanges() {
    // Obtém o tipo de transmissão selecionado no menu-list
    const selectedMenuItem = document.querySelector('.menu-item.active');
    const transmissionType = selectedMenuItem ? selectedMenuItem.getAttribute('data-value') : null;
    //ir buscar id ao url "http://192.168.59.33:5000/edit_channels?channel_id=1"
    const urlParams = new URLSearchParams(window.location.search);
    const channel_id = urlParams.get('channel_id');
    // Verifica se o channel_id foi obtido corretamente
    if (!channel_id) {
        alert("Erro ao obter o ID do canal.");
        return;
    }

    // Obtém a lista de reprodução ou o streaming selecionado em section-rightCH
    let selectedSource = null;
    if (transmissionType === "LOCAL") {
        const selectedItems = document.querySelectorAll('.playlist-container input[type="checkbox"]:checked, .songs-container input[type="checkbox"]:checked');
        const sources = Array.from(selectedItems).map(item => {
            if (item.id.startsWith('playlist-')) {
                return `PLAYLIST:${item.id.replace('playlist-', '')}`;
            } else if (item.id.startsWith('song-')) {
                return `SONG:${item.id.replace('song-', '')}`;
            }
        }).filter(source => source !== null); // Filter out null values

        selectedSource = sources.length > 0 ? sources.join(';') : null;
    
    } else if (transmissionType === "STREAMING") {
        const selectedStreaming = document.querySelector('.streaming-container input[type="checkbox"]:checked');
        selectedSource = selectedStreaming ? selectedStreaming.id.replace('streaming-', '') : null;
    }


    // Dados a serem enviados para o backend
    const data = {
        channel_type: transmissionType,
        channel_reproduction: selectedSource,
        channel_id: channel_id
        
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
            alert("Settings saved successfully!");
            // refresh page
            location.reload();
        } else {
            console.error("Error saving settings:", response.statusText);
            alert("Error saving settings.");
        }
    })
    .catch(error => {
        console.error("Erro ao salvar as configurações:", error);
        alert("Erro ao salvar as configurações.");
    });
}

function toggleStreamingSelection(item) {
    const allItems = document.querySelectorAll('.streaming-item');

    // Deselect all items
    allItems.forEach(i => {
        i.querySelector('.selection-icon').classList.remove('selected');
    });

    // Select the clicked item
    const icon = item.querySelector('.selection-icon');
    icon.classList.add('selected');

    // Update the selected streaming source display
    const selectedDisplay = document.getElementById("selectedStreamingDisplay");
    const hintMessage = document.querySelector(".section-hint");

    if (hintMessage) {
        hintMessage.style.display = "none";
    }

    selectedDisplay.innerHTML = `
        <div class="streaming-selected-box">
            <span class="streaming-label">Fonte Selecionada:</span>
            <span class="streaming-name-selected">${item.textContent.trim()}</span>
        </div>
    `;
}

// Add this function to toggle channel edit mode if it doesn't exist already
function toggleChannelEdit() {
    const displayElement = document.querySelector('.playlist-title-container');
    const editForm = document.getElementById('channelEditForm');
    
    if (editForm.style.display === 'none') {
        editForm.style.display = 'flex';
        displayElement.style.opacity = '0.5';
    } else {
        editForm.style.display = 'none';
        displayElement.style.opacity = '1';
    }
    
    document.getElementById('channelNameInput').focus();
}

