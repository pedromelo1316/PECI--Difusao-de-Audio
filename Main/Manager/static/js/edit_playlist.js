function renamePlaylist(playlistName) {
    const newName = prompt('Enter new playlist name:', playlistName);

    if (newName && newName !== playlistName) {
        fetch(`/edit_playlist_by_name`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_name: playlistName, new_name: newName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the title using the new selector
                document.querySelector('.playlist-title').textContent = newName;
                // Show a success notification
                const notification = document.createElement('div');
                notification.className = 'success-notification';
                notification.textContent = 'Playlist renamed successfully!';
                document.body.appendChild(notification);
                setTimeout(() => {
                    notification.classList.add('show');
                    setTimeout(() => {
                        notification.classList.remove('show');
                        setTimeout(() => {
                            document.body.removeChild(notification);
                        }, 300);
                    }, 2000);
                }, 100);
            } else {
                alert('Error renaming playlist.');
            }
        })
        .catch(err => {
            alert('Error renaming playlist.');
        });
    }
}

function addSongToPlaylist(songName, playlistName) {
    fetch('/add_song_to_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_name: songName, playlist_name: playlistName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            
            const playlistName = document.querySelector('.playlist-title').textContent;
            loadPlaylistOrder(playlistName);
            
            location.reload();
        } else {
            alert(data.error || 'Erro ao adicionar música à playlist.');
        }
    })
    .catch(err => {
        alert('Erro ao adicionar música à playlist.');
        console.error(err);
    });
}

function removeSongFromPlaylist(songName, playlistName) {
    fetch('/remove_song_from_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_name: songName, playlist_name: playlistName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload playlist order to reflect the removal
            const playlistName = document.querySelector('.playlist-title').textContent;
            loadPlaylistOrder(playlistName);
           
            location.reload();
        } else {
            alert(data.error || 'Error removing song from playlist.');
        }
    })
    .catch(err => {
        alert('Error removing song from playlist.');
        console.error(err);
    });
}

function toggleSong(icon, songName, playlistName) {
    const action = icon.classList.contains('fa-check') ? 'remove' : 'add';
    fetch(`/edit_playlist/${playlistName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_name: songName, action: action })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            icon.classList.toggle('fa-check');
            icon.classList.toggle('fa-square');
            const playlistList = document.getElementById('playlist-list');
            if (action === 'add') {
                const newIndex = playlistList.querySelectorAll('li').length + 1;
                const li = document.createElement('li');
                li.className = 'playlist-item';
                li.draggable = true;
                li.dataset.song = songName;
                li.innerHTML = `<span>${newIndex}. ${songName}</span>`;
                playlistList.appendChild(li);
            } else {
                const items = playlistList.querySelectorAll('li');
                items.forEach(item => {
                    if (item.dataset.song === songName) {
                        playlistList.removeChild(item);
                    }
                });
            }
            updatePlaylistOrder();
        } else {
            alert('Error updating playlist.');
        }
    });
}

function savePlaylistAndRedirect(playlistName) {
    // Obter as músicas da playlist atual
    const playlistItems = document.querySelectorAll('#playlist-list .playlist-item');
    const updatedSongs = Array.from(playlistItems).map(item => item.getAttribute('data-song'));

    fetch('/save_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_name: playlistName, songs: updatedSongs })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Playlist saved successfully!');
            window.location.href = '/secundaria'; // Redireciona para a página principal ou outra página
        } else {
            alert(data.error || 'Error saving playlist.');
        }
    })
    .catch(err => {
        alert('Error saving playlist.');
        console.error(err);
    });
}

function loadPlaylistOrder(playlistName) {
    fetch(`/playlist_order/${playlistName}`)
        .then(res => res.json())
        .then(data => {
            const playlistList = document.getElementById('playlist-list');
            playlistList.innerHTML = '';
            data.songs.forEach((song, index) => {
                const li = document.createElement('li');
                li.className = 'playlist-item';
                li.draggable = true;
                li.dataset.song = song;
                li.innerHTML = `<span>${index + 1}. ${song}</span>
                    <i class="fa-solid fa-trash" onclick="removeSongFromPlaylist('${song}', '${playlistName}')" title="Remove song"></i>`;
                playlistList.appendChild(li);
            });
            // Atualiza os ícones e reatribui eventos após DOM update
            updateSongIcons();
            rebindSongItemEvents();
        })
        .catch(err => {
            console.error('Erro ao carregar a playlist:', err);
        });
}

function updateSongIcons() {
    const playlistSongs = Array.from(
        document.querySelectorAll('#playlist-list .playlist-item')
    ).map(li => li.dataset.song);

    document.querySelectorAll('#songs-list .song-item').forEach(item => {
        const songName = item.querySelector('span').textContent;
        const icon = item.querySelector('i');
        icon.classList.remove('fa-check', 'fa-square');
        if (playlistSongs.includes(songName)) {
            icon.classList.add('fa-check');
        } else {
            icon.classList.add('fa-square');
        }
    });
}

// Reatribui eventos de clique para os ícones das músicas após update do DOM
function rebindSongItemEvents() {
    document.querySelectorAll('#songs-list .song-item i').forEach(icon => {
        icon.onclick = function() {
            const li = this.closest('.song-item');
            const songName = li.querySelector('span').textContent;
            const playlistName = document.querySelector('.playlist-title').textContent;
            if (this.classList.contains('fa-check')) {
                removeSongFromPlaylist(songName, playlistName);
            } else {
                addSongToPlaylist(songName, playlistName);
            }
        };
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const playlistList = document.getElementById('playlist-list');

    let draggedItem = null;

    playlistList.addEventListener('dragstart', (event) => {
        draggedItem = event.target;
        event.dataTransfer.effectAllowed = 'move';
    });

    playlistList.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    playlistList.addEventListener('drop', (event) => {
        event.preventDefault();
        if (event.target.classList.contains('playlist-item') && draggedItem !== event.target) {
            playlistList.insertBefore(draggedItem, event.target.nextSibling);
            updatePlaylistOrder();
        }
    });

    // Fix the playlist name selector for the updated DOM structure
    const playlistName = document.querySelector('.playlist-title').textContent;
    loadPlaylistOrder(playlistName);
    // Não precisa de event delegation, pois rebindSongItemEvents faz o trabalho após cada update
});

function updatePlaylistOrder() {
    const playlistItems = document.querySelectorAll('#playlist-list .playlist-item');
    playlistItems.forEach((item, index) => {
        item.querySelector('span').textContent = `${index + 1}. ${item.dataset.song}`;
    });
}

// Função para fechar o modal
function closeSongModal() {
    const modal = document.getElementById('song-modal');
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error('Modal com id "song-modal" não encontrado.');
    }
}

// Função para salvar a música
function saveSong() {
    const songName = document.getElementById('song-name').value;
    const songFile = document.getElementById('song-file').files[0];

    console.log("Nome da música:", songName);
    console.log("Arquivo da música:", songFile);

    if (!songName) {
        alert("The song name is required.");
        return;
    }

    if (!songFile) {
        alert('O arquivo de música é obrigatório.');
        return;
    }

    const formData = new FormData();
    formData.append('name', songName);
    formData.append('file', songFile);

    fetch('/add_song', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Song saved successfully!');
            closeSongModal();
            window.location.reload(); // Recarrega a página para atualizar a lista de músicas
        } else {
            alert(data.error || 'Erro ao salvar a música.');
        }
    })
    .catch(err => {
        console.error('Erro ao salvar a música:', err);
        alert('Erro ao salvar a música.');
    });
}

function importPlaylist(playlistName) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "audio/*";
    fileInput.multiple = true;

    fileInput.onchange = function () {
        const songFiles = fileInput.files;
        if (!songFiles || songFiles.length === 0) {
            alert("É necessário selecionar pelo menos um arquivo de música.");
            return;
        }

        if (!playlistName) {
            alert("O nome da playlist é obrigatório.");
            return;
        }

        const formData = new FormData();
        formData.append('playlist_name', playlistName);
        Array.from(songFiles).forEach(songFile => {
            formData.append('files[]', songFile);
        });

        fetch('/import_playlist', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Playlist criada com sucesso!');
                window.location.reload();
            } else {
                const errorMessages = data.errors.map(error => `${error.file}: ${error.error}`).join('\n');
                alert(`Erro ao adicionar as músicas:\n${errorMessages}`);
            }
        })
        .catch(err => {
            console.error('Erro ao adicionar as músicas:', err);
            alert('Erro ao comunicar com o servidor.');
        });
    };

    fileInput.click();
}