function updateSectionRight(value) {
    const sectionRight = document.getElementById("sectionRightContent");
    const saveButtonContainer = document.getElementById("saveButtonContainer");

    if (value === "local") {
        if (value === "local") {
            let playlistsHTML = '';
            for (const [playlistName, songs] of Object.entries(playlistsData)) {
                let songList = songs.map(song => `<li>${song}</li>`).join('');
                playlistsHTML += `
                    <div class="playlist-block">
                        <h4>${playlistName}</h4>
                        <ul>${songList}</ul>
                    </div>
                `;
            }
        
            sectionRight.innerHTML = `
                <div class="inner-section-left">
                    <h4>Para reprodução</h4>
                    <p>Seleciona uma playlist abaixo</p>
                </div>
                <div class="inner-section-right">
                    <h3>Playlists Disponíveis</h3>
                    <div class="playlist-container">
                        ${playlistsHTML}
                    </div>
                </div>
            `;
            sectionRight.style.display = 'flex';
            saveButtonContainer.style.display = "flex";
        }
        
    } else if (value === "streaming") {
        sectionRight.innerHTML = `
            <div class="inner-section-left">
                <h4>Streaming em reprodução</h4>
                <p>Em breve: integração com fontes de streaming.</p>
            </div>
            <div class="inner-section-right">
                <h4>Streaming Disponível</h4>
                <p>Lista de fontes ainda não implementada.</p>
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

document.querySelectorAll('input[name="tipo_transmissao"]').forEach(radio => {
    radio.addEventListener('change', function () {
        updateSectionRight(this.value);
    });
});


window.addEventListener('DOMContentLoaded', () => {
    const selected = document.querySelector('input[name="tipo_transmissao"]:checked');
    if (selected) {
        updateSectionRight(selected.value);
    }
});

