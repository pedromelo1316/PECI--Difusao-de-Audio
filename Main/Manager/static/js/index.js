document.addEventListener('DOMContentLoaded', loadPlaylists);

function loadPlaylists() {
    fetch('/playlists')
        .then(response => response.json())
        .then(data => {
            const playlistsList = document.getElementById('playlists-list');
            playlistsList.innerHTML = '';
            data.forEach(playlist => {
                const li = document.createElement('li');
                li.className = 'playlist-item2';
                li.innerHTML = `
                    <span>${playlist.name}</span>
                    <div class="playlist-actions">
                        <i class="fa-solid fa-pen" style="font-size: 16px; color: gray;" onclick="editPlaylist(${playlist.id}, '${playlist.name}')"></i>
                        <i class="fa-solid fa-trash" style="font-size: 16px; color: gray; onclick="deletePlaylist(${playlist.id})"></i>
                    </div>
                `;
                playlistsList.appendChild(li);
            });
            const addPlaylistItem = document.createElement('li');
            addPlaylistItem.className = 'playlist-item2 add-playlist';
            addPlaylistItem.onclick = addPlaylist;
            addPlaylistItem.innerHTML = '<span>Add +</span>';
            playlistsList.appendChild(addPlaylistItem);
        })
        .catch(err => console.error('Erro ao carregar playlists:', err));
}

function addPlaylist() {
    showCustomModal("Add Playlist", "Enter the name of the new playlist:", true, function (playlistName) {
        if (!playlistName) return;

        fetch('/add_playlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: playlistName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Playlist added successfully!");
                window.location.reload();
            } else {
                alert(data.error || "Erro ao adicionar a playlist.");
            }
        })
        .catch(err => {
            console.error("Erro ao adicionar a playlist:", err);
            alert("Erro ao comunicar com o servidor.");
        });
    });
}

let editingSongId = null;


// Mostrar modal para adicionar música


// Mostrar modal para editar música


// Fechar modal
function closeSongModal() {
    document.getElementById('song-modal').style.display = 'none';
}

// Salvar música (adicionar ou editar)
function saveSong() {
    const songName = document.getElementById('song-name').value;
    if (!songName) {
        alert('O nome da música é obrigatório');
        return;
    }

    const url = editingSongId ? `/edit_song/${editingSongId}` : '/add_song';
    const method = editingSongId ? 'POST' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: songName })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadSongs();
                closeSongModal();
            } else {
                alert(data.error || 'Erro ao salvar a música');
            }
        });
}

// Excluir música
function deleteSong(id) {
    if (!confirm('Tem certeza que deseja excluir esta música?')) return;

    fetch(`/delete_song/${id}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadSongs();
            } else {
                alert(data.error || 'Erro ao excluir a música');
            }
        });
}

// Carregar músicas ao carregar a página
document.addEventListener('DOMContentLoaded', loadSongs);



/////////////////////////////////////////////////


document.getElementById('streamForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Impede o envio padrão do formulário
    const formData = new FormData(this);

    fetch(this.action, {
        method: this.method,
        body: formData
    })
    .then(response => {
        if (response.ok) {
            alert('Link de transmissão salvo com sucesso!');
        } else {
            response.text().then(text => alert('Erro: ' + text));
        }
    })
    .catch(error => {
        alert('Erro ao salvar o link de transmissão.');
        console.error('Erro:', error);
    });
});






document.getElementById('streamForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Impede o envio padrão do formulário
    const formData = new FormData(this);

    fetch(this.action, {
        method: this.method,
        body: formData
    })
    .then(response => {
        if (response.ok) {
            alert('Link de transmissão salvo com sucesso!');
        } else {
            response.text().then(text => alert('Erro: ' + text));
        }
    })
    .catch(error => {
        alert('Erro ao salvar o link de transmissão.');
        console.error('Erro:', error);
    });
});


function showStreamModal() {
    document.getElementById('streamModal').style.display = 'block';
}

function closeStreamModal() {
    document.getElementById('streamModal').style.display = 'none';
}

function saveStream() {
    const streamName = document.getElementById('streamName').value;
    const streamUrl = document.getElementById('streamUrl').value;

    if (streamName && streamUrl) {
        // Enviar os dados para o backend
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/save_stream_url';

        const nameInput = document.createElement('input');
        nameInput.type = 'hidden';
        nameInput.name = 'stream_name';
        nameInput.value = streamName;

        const urlInput = document.createElement('input');
        urlInput.type = 'hidden';
        urlInput.name = 'stream_url';
        urlInput.value = streamUrl;

        const channelInput = document.createElement('input');
        channelInput.type = 'hidden';
        channelInput.name = 'channel_id';
        channelInput.value = '2';

        form.appendChild(nameInput);
        form.appendChild(urlInput);
        form.appendChild(channelInput);

        document.body.appendChild(form);
        form.submit();
    } else {
        alert('Please fill in all fields.');
    }
}






// Função para abrir o pop-up personalizado com suporte para Enter
function showCustomModal(title, message, showInput = false, callback) {
    document.getElementById("modal-title").innerText = title;
    document.getElementById("modal-message").innerText = message;
    const inputField = document.getElementById("modal-input");
    const modalConfirmButton = document.getElementById("modal-confirm");

    if (showInput) {
        inputField.style.display = "block";
        inputField.value = "";
        inputField.focus(); // Focar no campo automaticamente
    } else {
        inputField.style.display = "none";
    }

    document.getElementById("customModal").style.display = "block";

    function confirmAction() {
        let inputValue = showInput ? inputField.value.trim() : null;
        closeCustomModal();
        if (callback) callback(inputValue);
    }

    // Botão "OK" chama a ação de confirmação
    modalConfirmButton.onclick = confirmAction;

    // Enter também confirma a ação
    document.onkeydown = function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            confirmAction();
        }
    };
}
// Função para fechar o modal e remover evento de tecla
function closeCustomModal() {
    document.getElementById("customModal").style.display = "none";
    document.onkeydown = null; // Remover evento de tecla global
}

//function editPlaylist(playlistId, currentName) {
    // const newName = prompt('Digite o novo nome da playlist:', currentName);
    // if (!newName || newName === currentName) return;
    //fetch(`/edit_playlist/${playlistId}`, {
     //   method: 'POST',
       // headers: { 'Content-Type': 'application/json' },
       // body: JSON.stringify({ name: newName })
    //})
    //.then(response => response.json())
    //.then(data => {
     //   if (data.success) {
         //   loadPlaylists();
        //} else {
       //     alert(data.error || 'Erro ao renomear playlist.');
      //  }
    //})
  //  .catch(err => console.error('Erro ao renomear playlist:', err));
//}

function editPlaylist(playlistId) {
    if (!playlistId) {
        console.error("ID da playlist não fornecido.");
        showCustomModal("Erro", "ID da playlist não foi fornecido.");
        return;
    }

    console.log("Editando playlist com ID:", playlistId);
    // Redireciona para a página de edição da playlist específica
    window.location.href = `/edit_playlist/${playlistId}`;
}



// Função para guardar a playlist (Enter agora funciona)
function savePlaylist(playlistName) {
    fetch('/save_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: playlistName })
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            showCustomModal("Erro", "Erro ao guardar a playlist.");
        }
    })
    .catch(err => {
        showCustomModal("Erro", "Erro ao guardar a playlist.");
    });
}

// Substituir prompt por modal para adicionar música
function showAddSongModal() {
    showCustomModal("Add Music", "Enter the name of the song", true, function (songName) {
        if (!songName) return;

        // Criar input de ficheiro dinamicamente
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "audio/*";

        fileInput.onchange = function () {
            const songFile = fileInput.files[0];
            if (!songFile) {
                alert("O arquivo de música é obrigatório.");
                return;
            }

            const formData = new FormData();
            formData.append('name', songName); // Nome da música
            formData.append('file', songFile); // Arquivo de música

            fetch('/add_song', {
                method: 'POST',
                body: formData // Envia o FormData diretamente
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Música adicionada com sucesso!');
                    window.location.reload();
                } else {
                    alert(data.error || 'Erro ao adicionar a música.');
                }
            })
            .catch(err => {
                console.error('Erro ao adicionar a música:', err);
                alert('Erro ao comunicar com o servidor.');
            });
        };

        fileInput.click(); // Simula o clique para abrir o seletor de arquivos
    });
}

// Substituir prompt por modal para editar música
function editSong(songId, currentName) {
    showCustomModal("Editar Música", "Enter the new song name:", true, function (newName) {
        if (!newName || newName === currentName) return;

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
                    showCustomModal("Erro", "Erro ao atualizar o nome da música.");
                }
            })
            .catch(err => {
                showCustomModal("Erro", "Erro ao atualizar o nome da música.");
            });
        }
    });
}

// Substituir confirm padrão ao eliminar música
function deleteSong(songname) {
    showCustomModal("Eliminar Música", "Are you sure you want to delete this song?", false, function () {
        console.log("Deleting song:", songname);
        fetch(`/delete_song/${songname}`, { method: 'DELETE' })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                showCustomModal("Erro", "Erro ao eliminar a música.");
            }
        })
        .catch(err => {
            showCustomModal("Erro", "Erro ao eliminar a música.");
        });
    });
}

function deletePlaylist(playlistId) {
    if (!confirm('Are you sure you want to delete this playlist?')) return;
    fetch(`/delete_playlist/${playlistId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadPlaylists();
            } else {
                alert(data.error || 'Erro ao excluir playlist.');
            }
        })
        .catch(err => console.error('Erro ao excluir playlist:', err));
}


// Editar link de streaming
function editStreamingLink(element) {
    const listItem = element.closest(".streaming-item");
    const linkElement = listItem.querySelector("a");

    showCustomModal("Editar Link", "Edite o link de transmissão:", true, function (newLink) {
        if (!newLink || !isValidURL(newLink)) {
            showCustomModal("Erro", "Please enter a valid link.");
            return;
        }
        linkElement.href = newLink;
        linkElement.textContent = newLink;
    });
}

// Eliminar link de streaming
function deleteStreamingLink(element) {
    showCustomModal("Eliminar Link", "Tem a certeza que deseja apagar este link?", false, function () {
        const listItem = element.closest(".streaming-item");
        listItem.remove();
    });
}

// Função para validar URLs



function showAddStreamModal() {
    showCustomModal("Adicionar Link de Transmissão", "Enter the Streaming Name: ", true, function (streamName) {
        if (!streamName) {
            showCustomModal("Erro", "Streaming name is required.");
            return;
        }

        showCustomModal("Adicionar Link de Transmissão", "Enter the streaming link:", true, function (streamUrl) {
            if (!streamUrl || !isValidURL(streamUrl)) {
                showCustomModal("Erro", "Please enter a valid link.");
                return;
            }

            fetch('/save_stream_url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stream_name: streamName, stream_url: streamUrl, channel_id: 2 })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || "Erro desconhecido");
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert("Streaming link added successfully!");
                    window.location.reload();
                } else {
                    showCustomModal("Erro", data.error || "Erro ao adicionar o link de transmissão.");
                }
            })
            .catch(err => {
                console.error("Erro ao adicionar o link de transmissão:", err);
                showCustomModal("Erro", err.message || "Erro ao comunicar com o servidor.");
            });
        });
    });
}

// Função para validar URLs
function isValidURL(url) {
    const pattern = new RegExp('^(https?:\\/\\/)?' + // protocolo
        '((([a-zA-Z0-9\\-]+\\.)+[a-zA-Z]{2,})|' + // domínio
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // ou IP
        '(\\:\\d+)?(\\/[-a-zA-Z0-9%_.~+]*)*' + // porta e caminho
        '(\\?[;&a-zA-Z0-9%_.~+=-]*)?' + // query string
        '(\\#[-a-zA-Z0-9_]*)?$', 'i'); // fragmento
    return !!pattern.test(url);
}


function toggleChannelEdit() {
    const display = document.getElementById('channelTitleDisplay');
    const form = document.getElementById('channelEditForm');
    display.style.display = (display.style.display === 'none') ? 'flex' : 'none';
    form.style.display = (form.style.display === 'none') ? 'flex' : 'none';
}


function toggleColumnDetails(element) {
    // Garante que estamos a trabalhar com o item inteiro
    const columnItem = element.closest('.column-itemCH');
    const details = columnItem.querySelector('.column-details');

    if (details.style.display === 'none' || details.style.display === '') {
        details.style.display = 'block';
    } else {
        details.style.display = 'none';
    }
}

function editStreaming(streamingId) {
    if (!streamingId) {
        console.error("ID do streaming não fornecido.");
        showCustomModal("Erro", "ID do streaming não foi fornecido.");
        return;
    }

    console.log("Editando streaming com ID:", streamingId);
    // Redireciona para a página de edição do streaming específico
    window.location.href = `/edit_streaming/${streamingId}`;
}

function deleteStreaming(streamingId) {
    if (!confirm('Tem certeza que deseja excluir este link de streaming?')) return;

    fetch(`/delete_streaming/${streamingId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadStreamingLinks();
            } else {
                alert(data.error || 'Erro ao excluir o link de streaming.');
            }
        })
        .catch(err => console.error('Erro ao excluir o link de streaming:', err));
}

document.addEventListener('DOMContentLoaded', loadStreamingLinks);



function fetchMicrophones() {
    fetch('/update_microphones')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Microphones fetched successfully:', data.microphones);
                const microphoneSection = document.querySelector('.microfone-section');
                microphoneSection.innerHTML = `
                    <ul id="microphone-list">
                        ${data.microphones.map(mic => `
                            <li class="microfone-item">
                                <span>${mic.name} (Shortcut: ${mic.short_cut})</span>
                                <div class="microfone-actions">
                                    <i class="fa-solid fa-pen" onclick="editMicrofone('${mic.id}', '${mic.name}', '${mic.short_cut}')"></i>
                                    <i class="fa-solid fa-trash" onclick="deleteMicrofone('${mic.name}')"></i>
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                    <div style="text-align: center;">
                        <button onclick="fetchMicrophones()">Get Microfones</button>
                    </div>
                `;
            } else if (data.error) {
                console.error('Failed to fetch microphones:', data.error);
                alert('Failed to fetch microphones: ' + data.error);
            } else {
                console.error('Failed to fetch microphones:', data.error || 'Unknown error');
            }
        })
        .catch(error => console.error('Error fetching microphones:', error));
}

function editMicrofone(micId, currentName, currentShortcut) {
    showCustomModal("Edit Microphone", "Update the microphone Name (leave empty to skip):", true, function (newName) {
        if (newName === "") newName = currentName;

        showCustomModal("Edit Shortcut", "Enter a shortcut (0-9, leave empty to skip):", true, function (newShortcut) {
            if (newShortcut === "") newShortcut = currentShortcut;
            if (isNaN(newShortcut) || newShortcut < 0 || newShortcut > 9) {
                alert("Invalid shortcut. Please enter a number between 0 and 9.");
                return;
            }

            fetch(`/update_microphone/${micId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName, short_cut: newShortcut })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Microphone updated successfully!");
                    fetchMicrophones();
                } else {
                    alert(data.error || "Error updating microphone.");
                }
            })
            .catch(err => {
                console.error("Error updating microphone:", err);
                alert("Error communicating with the server.");
            });
        });
    });
}
