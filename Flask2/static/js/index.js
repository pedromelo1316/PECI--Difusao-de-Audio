function editPlaylist(playlistName) {
    window.location.href = `/edit_playlist/${playlistName}`;
}

function addPlaylist() {
    fetch('/get_songs')
    .then(response => response.json())
    .then(data => {
        if (data.songs.length === 0) {
            showErrorModal();
        } else {
            const playlistName = prompt('Nome da nova playlist:');
            if (playlistName) {
                window.location.href = `/edit_playlist/${playlistName}`;
            }
        }
    })
    .catch(err => {
        alert('Erro ao verificar músicas disponíveis.');
    });
}

function deleteSong(songId) {
    fetch(`/delete_song/${songId}`, {
        method: 'DELETE'
    }).then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Erro ao deletar a música.');
        }
    });
}

function showAddSongModal() {
    document.getElementById('addSongModal').style.display = 'block';
}

function closeAddSongModal() {
    document.getElementById('addSongModal').style.display = 'none';
}

function showErrorModal() {
    document.getElementById('errorModal').style.display = 'block';
}

function closeErrorModal() {
    document.getElementById('errorModal').style.display = 'none';
}

document.getElementById('addSongForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const songName = document.getElementById('songName').value;
    const songFile = document.getElementById('songFile').files[0];
    if (songName && songFile) {
        const formData = new FormData();
        formData.append('songName', songName);
        formData.append('songFile', songFile);

        fetch('/add_song', {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Erro ao adicionar a música.');
            }
        });
    }
});

function deletePlaylist(playlistName) {
    if (confirm("Tem certeza de que deseja eliminar a playlist '" + playlistName + "'?")) {
        fetch(`/delete_playlist/${playlistName}`, { method: 'DELETE' })
        .then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                alert('Erro ao eliminar a playlist.');
            }
        })
        .catch(err => {
            alert('Erro ao eliminar a playlist.');
        });
    }
}

function editSong(songId, currentName) {
    const newName = prompt("Editar nome da música:", currentName);
    if (newName && newName !== currentName) {
        fetch(`/update_song/${songId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName })
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert("Erro ao atualizar o nome da música.");
            }
        })
        .catch(err => {
            alert("Erro ao atualizar o nome da música.");
        });
    }
}

function syncMicrophone(micId) {
    fetch(`/sync_microphone/${micId}`, {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            alert('Microfone sincronizado com sucesso.');
        } else {
            alert('Erro ao sincronizar o microfone.');
        }
    });
}

function syncAllMicrophones() {
    fetch('/sync_all_microphones', {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            alert('Todos os microfones foram sincronizados com sucesso.');
        } else {
            alert('Erro ao sincronizar todos os microfones.');
        }
    });
}

function addMicrophone() {
    const micName = prompt('Nome do novo microfone:');
    if (micName) {
        fetch('/add_microphone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: micName })
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Erro ao adicionar o microfone.');
            }
        });
    }
}

function deleteMicrophone(micId) {
    if (confirm("Tem certeza de que deseja eliminar o microfone?")) {
        fetch(`/delete_microphone/${micId}`, { method: 'DELETE' })
        .then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                alert('Erro ao eliminar o microfone.');
            }
        })
        .catch(err => {
            alert('Erro ao eliminar o microfone.');
        });
    }
}
