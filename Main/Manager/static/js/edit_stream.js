function editStream(playlistName) {
    fetch(`/get_stream/${playlistName}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const newUrl = prompt("Link de streaming:", data.stream_url);
            if (newUrl && newUrl !== data.stream_url) {
                fetch(`/edit_stream/${data.playlist_id}`, {  // Usa o ID, não o nome
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ stream_url: newUrl })
                })
                .then(response => response.json())
                .then(update => {
                    if (update.success) {
                        alert("Link de streaming atualizado com sucesso!");
                        window.location.reload();
                    } else {
                        alert("Erro ao atualizar o link de streaming.");
                    }
                })
                .catch(err => {
                    alert("Erro ao comunicar com o servidor.");
                });
            }
        } else {
            alert("Erro ao obter o link do stream.");
        }
    })
    .catch(err => {
        alert("Erro ao comunicar com o servidor.");
    });
}
function deleteStream(playlistName) {
    if (confirm(`Tem certeza de que deseja eliminar o stream '${playlistName}'?`)) {
        fetch(`/get_stream/${playlistName}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fetch(`/delete_stream/${data.playlist_id}`, {  // Usa o ID, não o nome
                    method: 'DELETE'
                })
                .then(res => res.json())
                .then(response => {
                    if (response.success) {
                        alert("Stream eliminado com sucesso!");
                        window.location.reload();
                    } else {
                        alert("Erro ao eliminar o stream.");
                    }
                })
                .catch(err => {
                    alert("Erro ao comunicar com o servidor.");
                });
            } else {
                alert("Erro ao obter o ID do stream.");
            }
        })
        .catch(err => {
            alert("Erro ao comunicar com o servidor.");
        });
    }
}
