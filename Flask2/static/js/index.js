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



// Redirecionar para editar a playlist
function editPlaylist(playlistName) {
    if (playlistName) {
        window.location.href = `/edit_playlist/${playlistName}`;
    } else {
        showCustomModal("Erro", "Nome da playlist inválido.");
    }
}

// Criar nova playlist com suporte para Enter
function addPlaylist() {
    fetch('/get_songs')
        .then(response => response.json())
        .then(data => {
            if (data.songs.length === 0) {
                showCustomModal("Erro", "Não existem músicas disponíveis. Por favor, adicione músicas.", false);
            } else {
                showCustomModal("Adicionar Playlist", "Digite o nome da nova playlist:", true, function (playlistName) {
                    if (playlistName) {
                        window.location.href = `/edit_playlist/${playlistName}`;
                    }
                });
            }
        })
        .catch(err => {
            showCustomModal("Erro", "Erro ao verificar músicas disponíveis.");
        });
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
    showCustomModal("Adicionar Música", "Digite o nome da música:", true, function (songName) {
        if (!songName) return;

        // Criar input de ficheiro dinamicamente
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "audio/*";

        fileInput.onchange = function () {
            const songFile = fileInput.files[0];
            if (!songFile) return;

            const formData = new FormData();
            formData.append('songName', songName);
            formData.append('songFile', songFile);

            fetch('/add_song', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    showCustomModal("Erro", "Erro ao adicionar a música.");
                }
            })
            .catch(err => {
                showCustomModal("Erro", "Erro ao comunicar com o servidor.");
            });
        };

        fileInput.click(); // Simula o clique para abrir o seletor de ficheiros
    });
}

// Substituir prompt por modal para editar música
function editSong(songId, currentName) {
    showCustomModal("Editar Música", "Digite o novo nome da música:", true, function (newName) {
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
function deleteSong(songId) {
    showCustomModal("Eliminar Música", "Tem certeza de que deseja eliminar esta música?", false, function () {
        fetch(`/delete_song/${songId}`, { method: 'DELETE' })
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

// Substituir confirm padrão ao eliminar playlists
function deletePlaylist(playlistName) {
    showCustomModal("Eliminar Playlist", `Tem certeza de que deseja eliminar a playlist "${playlistName}"?`, false, function () {
        fetch(`/delete_playlist/${playlistName}`, { method: 'DELETE' })
            .then(res => {
                if (res.ok) {
                    window.location.reload();
                } else {
                    showCustomModal("Erro", "Erro ao eliminar a playlist.");
                }
            })
            .catch(err => {
                showCustomModal("Erro", "Erro ao eliminar a playlist.");
            });
    });
}

// Substituir prompts padrão ao adicionar um link de streaming
function addStreamingLink() {
    showCustomModal("Novo Link de Transmissão", "Insira o nome da transmissão:", true, function (name) {
        if (!name) return;
        
        showCustomModal("Novo Link de Transmissão", "Insira o link de transmissão:", true, function (link) {
            if (!link || !isValidURL(link)) {
                showCustomModal("Erro", "Por favor, insira um link válido.");
                return;
            }

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
        });
    });
}

// Editar link de streaming
function editStreamingLink(element) {
    const listItem = element.closest(".streaming-item");
    const linkElement = listItem.querySelector("a");

    showCustomModal("Editar Link", "Edite o link de transmissão:", true, function (newLink) {
        if (!newLink || !isValidURL(newLink)) {
            showCustomModal("Erro", "Por favor, insira um link válido.");
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
function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
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
