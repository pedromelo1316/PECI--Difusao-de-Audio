document.addEventListener("DOMContentLoaded", function () {
    const columnBox = document.getElementById("columnBox");

    window.toggleColumnDetails = function(icon) {
        
        const columnItem = icon.closest(".column-item");
        const details = columnItem.querySelector(".column-details");
        const isHidden = (details.style.display === 'none' || !details.style.display);
        details.style.display = isHidden ? 'block' : 'none';
    };

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.column-item').forEach(item => {
          item.addEventListener('click', e => {
            if (!e.target.closest('.column-actions')) {
              toggleColumnDetails(item.querySelector('.fa-chevron-down'));
            }
          });
        });
    });

    // Função para alternar seleção de colunas
    function toggleColumnSelection(column) {
        if (column.classList.contains("checked")) {
            column.classList.remove("checked");
            column.querySelector("span").innerHTML = column.querySelector("span").innerHTML.replace("✔ ", "");
        } else {
            column.classList.add("checked");
            column.querySelector("span").innerHTML = "✔ " + column.querySelector("span").innerHTML;
        }
    }

    // Função para adicionar uma nova coluna
    window.addColumn = function() {
        const columnList = document.querySelector(".column-list");
        const columnCount = columnList.querySelectorAll(".column-item").length; // Conta apenas colunas reais
        const newColumn = document.createElement("div");
    
        newColumn.classList.add("column-item");
        newColumn.innerHTML = `<div class="column-header">
                                   <span>Coluna ${columnCount + 1}</span>
                                   <div class="column-actions">
                                       <i class="fa-solid fa-chevron-down" onclick="toggleColumnDetails(this)"></i>
                                       <i class="fa-solid fa-trash" onclick="removeColumn(this)"></i>
                                   </div>
                               </div>
                               <div class="column-details" style="display: none;">
                                   <p>IP: 192.168.1.${columnCount + 1}</p>
                                   <p>MAC: 00:1A:2B:3C:4D:${(columnCount + 1).toString(16).padStart(2, '0')}</p>
                                   <p>Zona: Nenhuma</p>
                               </div>`;+
    
        // Adicionar a nova coluna antes do botão "+ Coluna"
        columnList.insertBefore(newColumn, document.querySelector(".add-column"));
    }
    
    // Global state to track used columns in zonas
    let usedZoneColumns = [];

    // Função para adicionar uma nova coluna dentro de uma zona
    function addZoneColumn(selectElement) {
        const selectedColumn = selectElement.value;
        if (!selectedColumn) return;

        const columnList = selectElement.closest(".column-list");
        const newColumn = document.createElement("div");
        newColumn.classList.add("column-item");
        newColumn.innerHTML = `
            <div class="column-header">
                <span>${selectedColumn}</span>
                <div class="column-actions">
                    <i class="fa-solid fa-chevron-down" onclick="toggleColumnDetails(this)"></i>
                    <i class="fa-solid fa-trash" onclick="removeColumn(this, '${selectedColumn}')"></i>
                </div>
            </div>
            <div class="column-details" style="display: none;">
                <!-- Details can be filled dynamically if needed -->
            </div>
        `;
        columnList.insertBefore(newColumn, selectElement.parentElement);
        // Replace select container back to the "Adicionar Coluna" button
        const addBtn = document.createElement("div");
        addBtn.classList.add("add-column");
        addBtn.innerHTML = `<span>+ Coluna</span>`;
        addBtn.addEventListener("click", function() {
            showSelectForZone(addBtn);
        });
        selectElement.parentElement.replaceWith(addBtn);

        // Mark column as used
        usedZoneColumns.push(selectedColumn);
    }

    // Helper: show select element to pick a column from Wi-Fi columns
    function showSelectForZone(buttonElement) {
        const container = document.createElement("div");
        container.classList.add("select-container");
        const select = document.createElement("select");
        select.classList.add("select-column");
        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        defaultOption.textContent = "Selecione uma coluna";
        select.appendChild(defaultOption);
        // Populate with available columns from Conexões Wi-Fi, filtering usedZoneColumns
        const wifiColumns = document.querySelectorAll("#columnBox .column-item");
        wifiColumns.forEach(column => {
            const colName = column.querySelector("span").textContent.replace("✔ ", "").trim();
            if (!usedZoneColumns.includes(colName)) {  // Only add if not used
                const option = document.createElement("option");
                option.value = colName;
                option.textContent = colName;
                select.appendChild(option);
            }
        });
        container.appendChild(select);
        // Replace the add button with the select container
        buttonElement.parentElement.replaceChild(container, buttonElement);
        // On selection change, add the zone column
        select.addEventListener("change", function () {
            addZoneColumn(select);
        });
    }

    // Aplicar funcionalidade ao botão "+ Coluna"
    document.querySelector(".add-column").addEventListener("click", addColumn);

    // Adicionar funcionalidade de seleção às colunas existentes
    document.querySelectorAll(".column-item").forEach(item => {
        item.addEventListener("click", function () {
            toggleColumnSelection(this);
        });
    });

    // Adicionar funcionalidade de remoção às colunas existentes
    document.querySelectorAll(".delete-column").forEach(btn => {
        btn.addEventListener("click", function (event) {
            event.stopPropagation(); // Impede a ativação da seleção ao clicar no ícone de lixo
            this.closest(".column-item").remove();
        });
    });

    // Controle de volume
    document.querySelectorAll("input[type='range']").forEach(slider => {
        slider.addEventListener("input", function () {
            const volumeLabel = this.nextElementSibling;
            volumeLabel.textContent = `Volume: ${this.value}%`;
        });
    });

    // Adicionar nova zona
    document.querySelector(".add-zone").addEventListener("click", function addZoneHandler() {
        const zoneName = prompt("Nome da zona:");
        if (!zoneName) return;

        const zoneContainer = document.querySelector(".zone-container");
        const clickedPlus = this;

        // Cria nova zona com a mesma estrutura de “Piscina”
        const newZone = document.createElement("div");
        newZone.classList.add("zone-box");
        newZone.innerHTML = `
            <div class="zone-header">
                <h3>${zoneName}</h3>
                <i class="fa-solid fa-trash delete-zone"></i>
            </div>
            <div class="zone-content">
                <div class="column-section">
                    <h4>Colunas</h4>
                    <div class="column-list">
                        <div class="add-column">
                            <span>+ Coluna</span>
                        </div>
                    </div>
                </div>
                <div class="channel-volume">
                    <div class="channel-section">
                        <h4>Canal</h4>
                        <div class="channel-options">
                            <label><input type="checkbox" name="channel-${zoneName}" value="1" onclick="selectSingleChannel(this)"> Canal 1</label>
                            <label><input type="checkbox" name="channel-${zoneName}" value="2" onclick="selectSingleChannel(this)"> Canal 2</label>
                            <label><input type="checkbox" name="channel-${zoneName}" value="3" onclick="selectSingleChannel(this)"> Canal 3</label>
                        </div>
                    </div>
                    <div class="volume-section">
                        <h4>Volume</h4>
                        <input type="range" min="0" max="100" value="50">
                        <p>${zoneName}</p>
                    </div>
                </div>
            </div>
        `;

        // Substitui o bloco "+" pela nova zona
        zoneContainer.replaceChild(newZone, clickedPlus);

        // Cria um novo bloco "+" e adiciona ao final
        const newAddZone = document.createElement("div");
        newAddZone.classList.add("zone-box", "add-zone");
        newAddZone.innerHTML = `<span>+</span>`;
        zoneContainer.appendChild(newAddZone);

        // Reanexa o evento ao novo "+"
        newAddZone.addEventListener("click", addZoneHandler);

        // Remover zona
        newZone.querySelector(".delete-zone").addEventListener("click", function() {
            newZone.remove();
            populateAddZoneSelects(); // Update the zone options when a zone is removed
        });

        // Ao clicar em “+ Coluna”, mostrar canal e volume
        const addColBtn = newZone.querySelector(".add-column");
        const columnList = newZone.querySelector(".column-list");
        const channelSection = newZone.querySelector(".channel-section");
        const volumeSection = newZone.querySelector(".volume-section");
        addColBtn.addEventListener("click", function() {
            showSelectForZone(addColBtn);
        });

        populateZoneOptions();
        populateAddZoneSelects(); // Update the zone options when a new zone is added
    });

    // Ensure only one channel can be selected per zone
    window.selectSingleChannel = function(checkbox) {
        const checkboxes = document.querySelectorAll(`input[name="${checkbox.name}"]`);
        checkboxes.forEach((cb) => {
            if (cb !== checkbox) cb.checked = false;
        });
    };

    // Ensure only one transmission type can be selected at a time
    document.querySelectorAll(".channel-options input[type='checkbox']").forEach(checkbox => {
        checkbox.addEventListener("click", function() {
            const checkboxes = this.closest(".channel-options").querySelectorAll("input[type='checkbox']");
            checkboxes.forEach(cb => {
                if (cb !== this) cb.checked = false;
            });
        });
    });

    // Populate zone options in channel selects
    function populateZoneOptions() {
        const zoneNames = Array.from(document.querySelectorAll(".zone-header h3")).map(zone => zone.textContent);
        const channelSelects = document.querySelectorAll(".channels-container select");
        channelSelects.forEach(select => {
            select.innerHTML = '<option value="" disabled>Selecione as zonas</option>';
            zoneNames.forEach(zoneName => {
                const option = document.createElement("option");
                option.value = zoneName;
                option.textContent = zoneName;
                select.appendChild(option);
            });
        });
    }

    // Populate zone options in the add zone selects
    function populateAddZoneSelects() {
        const zoneNames = Array.from(document.querySelectorAll(".zone-header h3")).map(zone => zone.textContent);
        const addZoneSelects = document.querySelectorAll("[id^='addZoneSelect']");
        addZoneSelects.forEach(select => {
            select.innerHTML = '<option value="" disabled selected>Adicionar Zona</option>';
            zoneNames.forEach(zoneName => {
                const option = document.createElement("option");
                option.value = zoneName;
                option.textContent = zoneName;
                select.appendChild(option);
            });
        });
    }

    // Update zones table based on selected zones
    function updateZonesTable() {
        const zonesChannel1 = Array.from(document.getElementById("channel1").selectedOptions).map(option => option.value).join(", ");
        const zonesChannel2 = Array.from(document.getElementById("channel2").selectedOptions).map(option => option.value).join(", ");
        const zonesChannel3 = Array.from(document.getElementById("channel3").selectedOptions).map(option => option.value).join(", ");
        document.getElementById("zonesChannel1").textContent = zonesChannel1;
        document.getElementById("zonesChannel2").textContent = zonesChannel2;
        document.getElementById("zonesChannel3").textContent = zonesChannel3;
    }

    // Add zone to channel
    window.addZoneToChannel = function(channelNumber) {
        const select = document.getElementById(`addZoneSelect${channelNumber}`);
        const zoneName = select.value;
        if (!zoneName) return;

        const zonesCell = document.getElementById(`zonesChannel${channelNumber}`);
        const currentZones = zonesCell.textContent ? zonesCell.textContent.split(", ") : [];
        if (!currentZones.includes(zoneName)) {
            currentZones.push(zoneName);
            zonesCell.textContent = currentZones.join(", ");
        }
    };

    // Remove zone from channel
    window.removeZoneFromChannel = function(channelNumber) {
        const zoneName = prompt("Nome da zona a remover:");
        if (!zoneName) return;

        const zonesCell = document.getElementById(`zonesChannel${channelNumber}`);
        let currentZones = zonesCell.textContent ? zonesCell.textContent.split(", ") : [];
        currentZones = currentZones.filter(zone => zone !== zoneName);
        zonesCell.textContent = currentZones.join(", ");
    };

    // Remove column
    window.removeColumn = function(icon, columnName) {
        const columnItem = icon.closest(".column-item");
        columnItem.remove();
        // If it was a zone column (columnName provided), free it up for reuse
        if (columnName) {
            usedZoneColumns = usedZoneColumns.filter(col => col !== columnName);
        }
    };

    // Toggle column details
    

    // Initial population of zone options
    populateAddZoneSelects();
    populateZoneOptions();

    // Add event listeners to update zones table when selections change
    document.getElementById("channel1").addEventListener("change", updateZonesTable);
    document.getElementById("channel2").addEventListener("change", updateZonesTable);
    document.getElementById("channel3").addEventListener("change", updateZonesTable);

    // Initial update of zones table
    updateZonesTable();
});

