function renamePlaylist(playlistName) {
    const newName = prompt('Novo nome da playlist:', playlistName);

    if (newName && newName !== playlistName) {
        fetch(`/edit_playlist_by_name`, { // Nova rota para buscar pelo nome
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_name: playlistName, new_name: newName }) // Envia o nome atual e o novo nome
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Atualiza o título do cabeçalho sem recarregar
                document.querySelector('.title h1').textContent = "Playlist " + newName;
            } else {
                alert('Erro ao renomear a playlist.');
            }
        })
        .catch(err => {
            alert('Erro ao renomear a playlist.');
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
            alert('Song successfully added to playlist!');
            location.reload(); // Recarrega a página para atualizar a lista
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
            alert('Song successfully removed from playlist!');
        location.reload(); // Recarrega a página para atualizar a lista
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
                li.innerHTML = `<span>${index + 1}. ${song}</span>`;
                playlistList.appendChild(li);
            });
        })
        .catch(err => {
            console.error('Erro ao carregar a playlist:', err);
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

    const playlistName = document.querySelector('.title h1').textContent.replace('Playlist ', '');
    loadPlaylistOrder(playlistName);
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