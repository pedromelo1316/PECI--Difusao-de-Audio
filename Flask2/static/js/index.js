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
