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

/*
function addStream() {
    const playlistName = prompt('Nome do novo stream:');
    if (!playlistName) return; // Se o utilizador cancelar, sair da função.

    fetch('/add_stream_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: playlistName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Redireciona para a edição do link de streaming da nova playlist.
            window.location.href = `/edit_stream/${data.playlist_id}`;
        } else {
            alert(data.error || "Erro ao criar a playlist.");
        }
    })
    .catch(err => {
        alert('Erro ao comunicar com o servidor.');
    });
}
*/

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


/*

function addStreamingLink() {
    const name = prompt("Insira o nome da transmissão:");
    if (!name) return;
    
    let link;
    do {
        link = prompt("Insira o link de transmissão:");
        if (!link) return;
        if (!isValidURL(link)) {
            alert("Por favor, insira um link válido \nTente novamente.");
        }
    } while (!isValidURL(link));
    
    const list = document.getElementById("streaming-list");
    const listItem = document.createElement("li");
    listItem.className = "streaming-item";
    listItem.innerHTML = `<strong>${name}</strong><a href="${link}" target="_blank">${link}</a>`;
    
    list.appendChild(listItem);
}

function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}*/

function addStreamingLink() {
    const name = prompt("Insira o nome da transmissão:");
    if (!name) return;
    
    let link;
    do {
        link = prompt("Insira o link de transmissão:");
        if (!link) return;
        if (!isValidURL(link)) {
            alert("Por favor, insira um link válido (exemplo: https://exemplo.com).\nTente novamente.");
        }
    } while (!isValidURL(link));
    
    const list = document.getElementById("streaming-list");
    const listItem = document.createElement("li");
    listItem.className = "streaming-item";
    listItem.innerHTML = `
        <strong>${name}</strong>
        <a href="${link}" target="_blank">${link}</a>
        <div class="actions">
            <i class="fa fa-pen" onclick="editStreamingLink(this)"></i>
            <i class="fa fa-trash" onclick="deleteStreamingLink(this)"></i>
        </div>
    `;
    
    list.appendChild(listItem);
}

function editStreamingLink(element) {
    const listItem = element.closest(".streaming-item");
    const linkElement = listItem.querySelector("a");
    let newLink;
    do {
        newLink = prompt("Edite o link de transmissão:", linkElement.href);
        if (!newLink) return;
        if (!isValidURL(newLink)) {
            alert("Por favor, insira um link válido.");
        }
    } while (!isValidURL(newLink));
    linkElement.href = newLink;
    linkElement.textContent = newLink;
}

function deleteStreamingLink(element) {
    if (confirm("Tem a certeza que deseja apagar este link?")) {
        const listItem = element.closest(".streaming-item");
        listItem.remove();
    }
}

function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}


/*
function editStream(playlistId) {
    window.location.href = `/edit_stream/${playlistId}`;
}


function deleteStream(playlistName) {
    if (confirm("Tem certeza de que deseja eliminar o stream '" + playlistName + "'?")) {
        fetch(`/delete_playlist/${playlistName}`, { method: 'DELETE' })
        .then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                alert('Erro ao eliminar o stream.');
            }
        })
        .catch(err => {
            alert('Erro ao eliminar o stream.');
        });
    }
}
*/


