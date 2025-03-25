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
            alert('Música adicionada à playlist com sucesso!');
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
            alert('Música removida da playlist com sucesso!');
            location.reload(); // Recarrega a página para atualizar a lista
        } else {
            alert(data.error || 'Erro ao remover música da playlist.');
        }
    })
    .catch(err => {
        alert('Erro ao remover música da playlist.');
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
            alert('Erro ao atualizar a playlist.');
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
            alert('Playlist salva com sucesso!');
            window.location.href = '/secundaria'; // Redireciona para a página principal ou outra página
        } else {
            alert(data.error || 'Erro ao salvar a playlist.');
        }
    })
    .catch(err => {
        alert('Erro ao salvar a playlist.');
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
