function updateSectionRight(value) {
    const sectionRight = document.getElementById("sectionRightContent");
    const saveButtonContainer = document.getElementById("saveButtonContainer");

    // Reset classes and display
    sectionRight.className = "inner-dual-section";
    sectionRight.style.display = 'flex';

    if (value === "local") {
        let playlistsHTML = '';
        for (const [playlistName, songs] of Object.entries(playlistsData)) {
            const songCount = songs.length;
            let songList = songs.map(song => `<div class="song-item"> ${song}</div>`).join('');
            
            playlistsHTML += `
                <div class="playlist-item" onclick="togglePlaylistSongs(this)">
                    <div class="playlist-name">
                        ${playlistName} <span class="song-count">(${songCount})</span>
                        <i class="fa-solid fa-chevron-down dropdown-icon"></i>
                    </div>
                    <div class="playlist-songs" style="display: none;">
                        ${songList}
                    </div>
                </div>
            `;
        }

        let songsHTML = '';
        allSongs.forEach(song => {
            songsHTML += `<div class="song-item"> ${song}</div>`;
        });
    
        sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h3>Lista de reprodução</h3>
                <div class="stats-container">
                    <div class="stat-item">
                        <span class="stat-value">0</span>
                        <span class="stat-label">Playlists</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">0</span>
                        <span class="stat-label">Músicas</span>
                    </div>
                </div>
                <div class="selected-playlist-info">
                    <p class="section-hint">Arraste uma playlist ou música</p>
                </div>
            </div>
            <div class="inner-section-right">
                <h3>Playlists Disponíveis</h3>
                <div class="stats-container">
                    <div class="stat-item">
                        <span class="stat-value">${Object.keys(playlistsData).length}</span>
                        <span class="stat-label">Playlists</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${allSongs.length}</span>
                        <span class="stat-label">Músicas</span>
                    </div>
                </div>
                <div class="playlist-container">
                    ${playlistsHTML}
                </div>
                <h3>Músicas Disponíveis</h3>
                <div class="songs-container">
                    ${songsHTML}
                </div>
            </div>
        `;
        sectionRight.style.display = 'flex';
        saveButtonContainer.style.display = "flex";
        enableDragAndDrop();
        
    } else if (value === "streaming") {
        let streamingHTML = '';
        streamingSources.forEach(source => {
            streamingHTML += `
                <div class="streaming-item">
                    <span>${source}</span>
                    <button class="remove-item-btn" onclick="removeStreamingSource('${source}')">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            `;
        });

        sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h3>Fontes de Streaming Selecionadas</h3>
                <div class="selected-streaming-info">
                    ${streamingHTML || '<p class="section-hint">Nenhuma fonte selecionada.</p>'}
                </div>
                <button class="add-streaming-btn" onclick="openAddStreamingModal()">Adicionar Fonte</button>
            </div>
            <div class="inner-section-right">
                <h3>Gerenciar Fontes de Streaming</h3>
                <p>Adicione ou remova fontes de streaming para personalizar sua experiência.</p>
            </div>
        `;
        sectionRight.style.display = 'flex';
        saveButtonContainer.style.display = "flex";
    } else {
        sectionRight.className = "inner-dual-section empty-message";
        sectionRight.innerHTML = `<p style="text-align:center;">Selecione o tipo de reprodução que pretende</p>`;
        saveButtonContainer.style.display = "none";
    }
}

function togglePlaylistSongs(playlistElement) {
    const songsContainer = playlistElement.querySelector('.playlist-songs');
    const icon = playlistElement.querySelector('.dropdown-icon');
    if (songsContainer.style.display === 'none') {
        songsContainer.style.display = 'block';
        icon.classList.add('expanded');
        playlistElement.classList.add('expanded');
    } else {
        songsContainer.style.display = 'none';
        icon.classList.remove('expanded');
        playlistElement.classList.remove('expanded');
    }
}

function updateLeftStats() {
    const dropZone = document.querySelector('.inner-section-left .selected-playlist-info');
    const addedPlaylists = dropZone.querySelectorAll('.playlist-item').length;
    const addedSongs = dropZone.querySelectorAll('.song-item').length;

    const statsContainer = document.querySelector('.inner-section-left .stats-container');
    statsContainer.innerHTML = `
        <div class="stat-item">
            <span class="stat-value">${addedPlaylists}</span>
            <span class="stat-label">Playlists</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${addedSongs}</span>
            <span class="stat-label">Músicas</span>
        </div>
    `;
}

function enableDragAndDrop() {
    const draggableItems = document.querySelectorAll('.playlist-item, .song-item');
    const dropZone = document.querySelector('.inner-section-left .selected-playlist-info');

    draggableItems.forEach(item => {
        item.setAttribute('draggable', true);

        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', item.outerHTML);
            e.dataTransfer.effectAllowed = 'move';
            item.classList.add('dragging');
        });

        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
        });
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const droppedHTML = e.dataTransfer.getData('text/plain');
        const droppedElement = document.createElement('div');
        droppedElement.innerHTML = droppedHTML;
        const newItem = droppedElement.firstElementChild;

        // Add a remove button to the item
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-item-btn';
        removeBtn.innerHTML = '<i class="fa-solid fa-trash-can"></i>'; // Changed to trash icon
        removeBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering other click events (like togglePlaylistSongs)
            removeItemFromPlaylist(this.parentElement);
        });
        newItem.appendChild(removeBtn);

        // Avoid duplicates
        const existingItems = Array.from(dropZone.querySelectorAll('.playlist-item, .song-item'));
        const isDuplicate = existingItems.some(item => {
            // Compare the content without the remove button
            const itemContent = item.innerHTML.replace(/<button class="remove-item-btn">.*?<\/button>/g, '');
            const newItemContent = newItem.innerHTML.replace(/<button class="remove-item-btn">.*?<\/button>/g, '');
            return itemContent === newItemContent;
        });
        
        if (!isDuplicate) {
            // No longer auto-expanding playlists when added
            dropZone.appendChild(newItem);
            enableDragAndDrop(); // Re-enable drag-and-drop for the new item
            updateLeftStats(); // Update the stats after adding a new item
        }
    });
}

// New function to remove items from the playlist
function removeItemFromPlaylist(item) {
    const dropZone = document.querySelector('.inner-section-left .selected-playlist-info');
    dropZone.removeChild(item);
    updateLeftStats();
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
        updateSectionRight('local');
    }
    enableDragAndDrop();
    updateLeftStats();
});

