document.addEventListener("DOMContentLoaded", function () {

    window.renameNode = function(nodeId) { // Torna a função global
        const newName = prompt("Digite o novo nome para o nó:");
        if (newName) {
            fetch(`/rename_node/${nodeId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ name: newName })
            })
            .then(response => {
                if (response.ok) {
                    alert("Nó renomeado com sucesso!");
                    location.reload(); // Recarrega a página para refletir a mudança
                } else {
                    response.text().then(text => alert("Erro ao renomear o nó: " + text));
                }
            })
            .catch(error => console.error('Erro:', error));
        }
    };


    const columnBox = document.getElementById("columnBox");

    window.toggleColumnDetails = function(icon) {
        const columnItem = icon.closest(".column-item");
        const details = columnItem.querySelector(".column-details");
        const isHidden = (details.style.display === 'none' || !details.style.display);
        details.style.display = isHidden ? 'block' : 'none';
    };

    window.editColumnName = function(icon) {
        const columnItem = icon.closest(".column-item");
        const columnNameSpan = columnItem.querySelector("span");
        const currentName = columnNameSpan.textContent;
        const newName = prompt("Edit column name:", currentName);
        if (newName && newName !== currentName) {
            columnNameSpan.textContent = newName;
            fetch(`/update_column_name`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_name: currentName, new_name: newName })
            }).then(response => {
                if (!response.ok) {
                    console.error("Erro ao atualizar o nome da coluna:", response.statusText);
                    alert("Erro ao atualizar o nome da coluna.");
                    columnNameSpan.textContent = currentName;
                }
            }).catch(error => {
                console.error("Error updating column name:", error);
                columnNameSpan.textContent = currentName;
            });
        }
    };

    document.querySelectorAll('input[type="radio"]').forEach((radio) => {
        radio.addEventListener('change', function(event) {
            event.preventDefault();
            const channelId = this.closest('form').id.split('_')[1];
            const form = document.getElementById(`form_${channelId}`);
            form.submit();
        });
    });

    document.querySelectorAll('input[type="radio"]').forEach((radio) => {
        radio.addEventListener('change', function(event) {
            event.preventDefault();
            const form = this.closest('form');
            form.submit();
        });
    });

    document.querySelectorAll('.volume-slider').forEach(slider => {
        slider.addEventListener('change', function(event) {
            event.preventDefault();
            let volume = this.value;
            let areaName = this.closest('form').querySelector('input[name="name"]').value;
            this.nextElementSibling.textContent = `Volume: ${volume}%`;
            fetch('/update_volume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `name=${encodeURIComponent(areaName)}&volume=${encodeURIComponent(volume)}`
            }).then(response => console.log(`Volume updated to ${volume}`));
        });
    });

    function addArea() {
        const areaName = prompt("Name of the new zone:");
        if (!areaName) {
            alert("The zone name is required!");
            return;
        }
        fetch('/add_area', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: areaName })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => { throw new Error(data.error); });
            }
            return response.json();
        })
        .then(data => {
            alert("Zone added successfully!");
            location.reload();
        })
        .catch(error => {
            alert("Error: " + error.message);
        });
    }

    document.getElementById("addAreaButton").addEventListener("click", addArea);

    let usedZoneColumns = [];
    document.querySelectorAll(".add-column-button").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            showSelectForZone(this);
        });
    });
    document.querySelectorAll(".delete-column-button").forEach(btn => {
        btn.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            const columnItem = this.closest(".column-item");
            removeZoneColumn(columnItem);
        });
    });
    document.querySelectorAll("input[type='range']").forEach(slider => {
        slider.addEventListener("input", function (event) {
            event.preventDefault();
            this.nextElementSibling.textContent = `Volume: ${this.value}%`;
        });
    });

    function showSelectForZone(buttonElement) {
        console.log("Adding column to zone");
        const container = document.createElement("div");
        container.classList.add("select-container");

        const select = document.createElement("select");
        select.classList.add("select-column");

        fetch("/get_free_nodes")
            .then(response => response.json())
            .then(nodes => {
                if (nodes.length === 0) {
                    const option = document.createElement("option");
                    option.value = "";
                    option.disabled = true;
                    option.selected = true;
                    option.textContent = "No speakers available";
                    select.appendChild(option);
                } else {
                    const initialOption = document.createElement("option");
                    initialOption.value = "";
                    initialOption.textContent = "Select a speaker";
                    initialOption.selected = true;
                    initialOption.disabled = true;
                    select.appendChild(initialOption);

                    nodes.forEach(node => {
                        const option = document.createElement("option");
                        option.value = node.name;
                        option.textContent = node.name;
                        select.appendChild(option);
                    });
                }

                // Automatically open the dropdown to show all options
                setTimeout(() => {
                    select.size = nodes.length > 0 ? nodes.length + 1 : 1;
                }, 0);
            })
            .catch(error => console.error("Error fetching nodes:", error));

        // When an option is selected, add the column to the zone
        select.addEventListener("change", function () {
            document.removeEventListener("click", handleClickOutside);
            addZoneColumn(this, buttonElement);
        });

        container.appendChild(select);
        buttonElement.replaceWith(container);

        // Hide dropdown when clicking outside
        function handleClickOutside(event) {
            if (!container.contains(event.target)) {
                container.replaceWith(buttonElement);
                document.removeEventListener("click", handleClickOutside);
            }
        }
        setTimeout(() => {
            document.addEventListener("click", handleClickOutside);
        }, 0);
    }

    function addZoneColumn(selectElement, buttonElement) {
        const selectedColumn = selectElement.value;
        if (!selectedColumn) return;
        const zoneName = selectElement.closest(".zone-box").querySelector("h3").textContent.trim();
        const columnList = selectElement.closest(".column-section").querySelector(".column-list");

        const columnItem = document.createElement("div");
        columnItem.classList.add("column-item");
        columnItem.dataset.column = selectedColumn;
        columnItem.dataset.zone = zoneName;
        columnItem.innerHTML = `
            <span>${selectedColumn}</span>
            <button class="delete-column-button">
                <i class="fa-solid fa-trash" style="color: black;"></i>
            </button>
        `;

        columnItem.querySelector(".delete-column-button").addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            removeZoneColumn(columnItem);
        });

        columnList.appendChild(columnItem);
        selectElement.parentElement.remove();

        // Check if there are still speakers available to add
        fetch("/get_free_nodes")
            .then(response => response.json())
            .then(nodes => {
                if (nodes.length > 0) {
                    const addColumnButton = document.createElement("div");
                    addColumnButton.classList.add("add-column-button");
                    addColumnButton.innerHTML = '<span>+ Speaker</span>';
                    addColumnButton.onclick = function() { showSelectForZone(this); };
                    selectElement.closest(".column-section").appendChild(addColumnButton);
                }
            })
            .catch(error => console.error("Error checking available speakers:", error));

        fetch("/add_column_to_zone", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ zone_name: zoneName, column_name: selectedColumn })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
                columnItem.remove();
                usedZoneColumns = usedZoneColumns.filter(name => name !== selectedColumn);
            }
        })
        .catch(error => console.error("Error adding speaker:", error));
    }

    function removeZoneColumn(columnElement) {
        const columnName = columnElement.dataset.column;
        const zoneName = columnElement.dataset.zone;
        console.log("Removing speaker:", columnName, "from zone:", zoneName);
        fetch("/remove_column_from_zone", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ zone_name: zoneName, column_name: columnName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Speaker removed successfully!");
                columnElement.remove();
            } else {
                console.error("Error removing speaker:", data.error);
                alert("Error: " + data.error);
            }
        })
        .catch(error => console.error("Error removing speaker:", error));
    }

    window.removeArea = function(areaName) {
        if (confirm(`Are you sure you want to delete the zone "${areaName}"?`)) {
            const form = document.getElementById(`remove-area-form-${areaName}`);
            if (form) {
                form.submit();
            } else {
                console.error(`Form for area ${areaName} not found`);
                // Alternative approach if form submission doesn't work
                fetch('/remove_area', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: areaName })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Zone deleted successfully!');
                        location.reload();
                    } else {
                        alert('Error deleting zone: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error deleting zone:', error);
                    alert('Error deleting zone. Please try again.');
                });
            }
        }
    };

    window.configureProgramming = function(channelId) {
        const url = `/configure_programming/${channelId}`;
        window.location.href = url;
    };

    window.interruptWithMicrophone = function(channelId) {
        if (confirm("Are you sure you want to interrupt the programming with the microphone?")) {
            fetch(`/interrupt_with_microphone/${channelId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => {
                if (response.ok) {
                    alert("Programming interrupted successfully!");
                } else {
                    alert("Failed to interrupt programming.");
                }
            })
            .catch(error => console.error("Error interrupting programming:", error));
        }
    };

    window.displayChannelOptions = function () {
        const channelSelector = document.getElementById("channelSelector");
        const channelOptions = document.getElementById("channelOptions");
        const selectedChannelId = channelSelector.value;

        // Clear previous options
        channelOptions.innerHTML = "";

        if (selectedChannelId) {
            // Dynamically add options for the selected channel
            channelOptions.innerHTML = `
                <button onclick="configureProgramming(${selectedChannelId})" class="configure-button">Configure Programming</button>
                <button onclick="interruptWithMicrophone(${selectedChannelId})" class="interrupt-button">Interrupt with Microphone</button>
            `;
        }
    };

    window.toggleChannelOptions = function(channelItem) {
        const options = channelItem.querySelector(".channel-options");
        const isHidden = (options.style.display === 'none' || !options.style.display);
        options.style.display = isHidden ? 'block' : 'none';
        
        // Add visual indication that the channel is selected
        document.querySelectorAll('.channel-item').forEach(item => {
            if (item !== channelItem) {
                item.classList.remove('selected');
                item.querySelector(".channel-options").style.display = 'none';
            }
        });
        
        if (isHidden) {
            channelItem.classList.add('selected');
        } else {
            channelItem.classList.remove('selected');
        }
    };

    window.editChannelName = function(icon, channelId) {
        const channelItem = icon.closest(".channel-item");
        const channelNameSpan = channelItem.querySelector("span");
        const currentName = channelNameSpan.textContent;
        const newName = prompt("Edit channel name:", currentName);
        
        if (newName && newName !== currentName) {
            channelNameSpan.textContent = newName;
            fetch(`/update_channel_name`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel_id: channelId, new_name: newName })
            }).then(response => {
                if (!response.ok) {
                    console.error("Error updating channel name:", response.statusText);
                    alert("Error updating channel name.");
                    channelNameSpan.textContent = currentName;
                }
            }).catch(error => {
                console.error("Error updating channel name:", error);
                channelNameSpan.textContent = currentName;
            });
        }
    };

});



// Channel transmission functionality
document.addEventListener("DOMContentLoaded", function() {
    // Channel selection and transmission
    const transmitButton = document.getElementById('transmitSelectedChannels');
    if (transmitButton) {
        transmitButton.addEventListener('click', function() {
            const selectedChannels = [];
            document.querySelectorAll('.channel-select-input:checked').forEach(checkbox => {
                selectedChannels.push(parseInt(checkbox.dataset.channelId));
            });
            
            if (selectedChannels.length === 0) {
                alert('Please select at least one channel for transmission.');
                return;
            }
            
            // Send the selected channels to the server
            fetch('/transmit_channels', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ channels: selectedChannels })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`Transmission started on channels: ${selectedChannels.join(', ')}`);
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error transmitting channels:', error);
                alert('Failed to start transmission. Please try again.');
            });
        });
    }
    
    // Quick select/deselect all channels
    const selectAllCheckbox = document.getElementById('select-all-channels');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            document.querySelectorAll('.channel-select-input').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
    }
});

// Channel transmission functionality
let activeChannels = new Set();

window.toggleChannelTransmission = function(channelId) {
    const channelCard = document.querySelector(`.channel-card[data-channel-id="${channelId}"]`);
    const statusIndicator = channelCard.querySelector('.status-indicator');
    const statusText = channelCard.querySelector('.status-text');
    const toggleButton = channelCard.querySelector('.toggle-transmission-btn i');
    
    if (activeChannels.has(channelId)) {
        // Deactivate the channel
        statusIndicator.classList.remove('active');
        statusText.textContent = 'Inactive';
        toggleButton.classList.remove('fa-pause');
        toggleButton.classList.add('fa-play');
        activeChannels.delete(channelId);

        // Notify the server to stop the transmission
        updateChannelTransmission(channelId, false);
    } else {
        // Activate the channel
        statusIndicator.classList.add('active');
        statusText.textContent = 'Active';
        toggleButton.classList.remove('fa-play');
        toggleButton.classList.add('fa-pause');
        activeChannels.add(channelId);

        // Notify the server to start the transmission
        updateChannelTransmission(channelId, true);
    }
};

function updateChannelTransmission(channelId, isActive) {
    fetch('/update_channel_transmission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            channel_id: channelId, 
            active: isActive 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error(`Failed to ${isActive ? 'activate' : 'deactivate'} channel:`, data.error);
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error updating channel transmission:', error);
        alert('Failed to update channel status. Please try again.');
    });
}

// Microphone device selection
document.addEventListener('DOMContentLoaded', function() {
    // Check if browser supports getUserMedia
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Get the microphone select element
        const micSelect = document.getElementById('mic-device-select');
        
        if (micSelect) {
            // Get available audio input devices
            navigator.mediaDevices.enumerateDevices()
                .then(devices => {
                    // Filter for audio input devices only
                    const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
                    
                    // Add each microphone to the select dropdown
                    audioInputDevices.forEach(device => {
                        const option = document.createElement('option');
                        option.value = device.deviceId;
                        option.text = device.label || `Microphone ${micSelect.options.length}`;
                        micSelect.appendChild(option);
                    });
                    
                    // If no microphones found, show message
                    if (audioInputDevices.length === 0) {
                        const option = document.createElement('option');
                        option.value = "";
                        option.text = "No microphones found";
                        option.disabled = true;
                        micSelect.appendChild(option);
                    } else {
                        // Select first microphone by default
                        micSelect.selectedIndex = 1;
                    }
                })
                .catch(err => {
                    console.error('Error getting audio devices:', err);
                    const option = document.createElement('option');
                    option.value = "";
                    option.text = "Error accessing microphones";
                    option.disabled = true;
                    micSelect.appendChild(option);
                });
                
            // Request microphone permission to get labels
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    // Stop the stream immediately after getting permission
                    stream.getTracks().forEach(track => track.stop());
                })
                .catch(err => {
                    console.error('Error accessing microphone:', err);
                });
        }
    }
});



// Completely rewritten microphone dropdown functionality
document.addEventListener('DOMContentLoaded', function() {
    const micDropdownToggle = document.getElementById('mic-dropdown-toggle');
    const micDeviceDropdown = document.getElementById('mic-device-dropdown');
    
    if (micDropdownToggle && micDeviceDropdown) {
        // Hide dropdown initially
        micDeviceDropdown.style.display = 'none';
        
        // Toggle dropdown when clicking the icon
        micDropdownToggle.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            // Toggle display
            if (micDeviceDropdown.style.display === 'block') {
                micDeviceDropdown.style.display = 'none';
                micDropdownToggle.classList.remove('active');
            } else {
                micDeviceDropdown.style.display = 'block';
                micDropdownToggle.classList.add('active');
            }
        });
        
        // Close dropdown when clicking elsewhere on the page
        document.addEventListener('click', function(event) {
            // Check if click is outside the dropdown and toggle button
            if (!micDeviceDropdown.contains(event.target) && event.target !== micDropdownToggle) {
                micDeviceDropdown.style.display = 'none';
                micDropdownToggle.classList.remove('active');
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const micDropdownToggle = document.getElementById('mic-dropdown-toggle');
    const micDeviceDropdown = document.getElementById('mic-device-dropdown');

    if (micDropdownToggle && micDeviceDropdown) {
        // Hide dropdown initially
        micDeviceDropdown.style.display = 'none';

        // Toggle dropdown when clicking the icon
        micDropdownToggle.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();

            // Toggle display
            const isVisible = micDeviceDropdown.style.display === 'block';
            micDeviceDropdown.style.display = isVisible ? 'none' : 'block';

            // Toggle rotation class for animation
            micDropdownToggle.classList.toggle('active', !isVisible);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (event) {
            if (!micDeviceDropdown.contains(event.target) && event.target !== micDropdownToggle) {
                micDeviceDropdown.style.display = 'none';
                micDropdownToggle.classList.remove('active');
            }
        });
    }

    // Populate microphone options dynamically
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const micSelect = document.getElementById('mic-device-select');
        if (micSelect) {
            navigator.mediaDevices.enumerateDevices()
                .then(devices => {
                    const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
                    if (audioInputDevices.length === 0) {
                        const option = document.createElement('option');
                        option.value = '';
                        option.textContent = 'No microphones found';
                        option.disabled = true;
                        micSelect.appendChild(option);
                    } else {
                        audioInputDevices.forEach(device => {
                            const option = document.createElement('option');
                            option.value = device.deviceId;
                            option.textContent = device.label || `Microphone ${micSelect.options.length + 1}`;
                            micSelect.appendChild(option);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error enumerating devices:', error);
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'Error accessing microphones';
                    option.disabled = true;
                    micSelect.appendChild(option);
                });
        }
    }
});


function editChannelName() {
    document.getElementById('channelTitleContainer').style.display = 'none';
    document.getElementById('channelEditContainer').style.display = 'flex';
}



function toggleChannelEdit() {
    document.getElementById("channelTitleDisplay").style.display = "none";
    document.getElementById("channelEditForm").style.display = "flex";
}

function saveChannelName() {
    const input = document.getElementById('channelNameInput');
    const title = document.getElementById('channelTitle');
    const newName = input.value.trim();

    if (!newName) {
        alert("O nome não pode estar vazio!");
        return;
    }

    title.textContent = newName;
    document.getElementById('channelTitleDisplay').style.display = 'flex';
    document.getElementById('channelEditForm').style.display = 'none';

    fetch(`/update_channel_name`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            channel_id: parseInt(document.querySelector('input[name="channel_id"]').value),
            new_name: newName
        })
    }).then(response => {
        if (!response.ok) {
            alert("Erro ao atualizar o nome.");
            input.value = title.textContent;
        }
    }).catch(error => {
        alert("Erro ao contactar o servidor.");
        console.error(error);
    });
}


document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll('input[name="tipo_transmissao"]');
    const sectionRight = document.getElementById("sectionRightContent");
    const saveButtonContainer = document.getElementById("saveButtonContainer");

    function updateSectionRight(value) {
        if (value === "local") {
            sectionRight.innerHTML = `
                <div class="inner-section-left">
                    <h4>Lista de reprodução</h4>
                    <p>Conteúdo da caixa da esquerda.</p>
                </div>
                <div class="inner-section-right">
                    <h4>Playlists Disponíveis</h4>
                    <p>Conteúdo da caixa da direita.</p>
                </div>
            `;
            saveButtonContainer.style.display = "flex";
        } else if (value === "streaming") {
            sectionRight.innerHTML = `
                <div class="inner-section-left">
                    <h4>Streaming em reprodução</h4>
                    <p>Conteúdo da caixa da esquerda.</p>
                </div>
                <div class="inner-section-right">
                    <h4>Streaming Disponível</h4>
                    <p>Conteúdo da caixa da direita.</p>
                </div>
            `;
            saveButtonContainer.style.display = "flex";
        } else {
            sectionRight.className = "inner-dual-section empty-message";
            sectionRight.innerHTML = `<p style="text-align:center;">Selecione o tipo de reprodução que pretende</p>`;
            saveButtonContainer.style.display = "none";
        }
    }

    radios.forEach(radio => {
        radio.addEventListener("change", function () {
            if (this.checked) {
                updateSectionRight(this.value);
            }
        });
    });

    const checkedRadio = document.querySelector('input[name="tipo_transmissao"]:checked');
    updateSectionRight(checkedRadio ? checkedRadio.value : null);
});

window.toggleDeviceDetails = function(icon) {
    const columnItem = icon.closest(".column-itemCH");
    const details = columnItem.querySelector(".column-detailsCH");

    if (details.style.display === "none" || !details.style.display) {
        details.style.display = "block";
    } else {
        details.style.display = "none";
    }
};

// Attach event listeners to chevron icons for devices
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".column-headerCH .fa-chevron-down").forEach(icon => {
        icon.addEventListener("click", function (event) {
            event.stopPropagation(); // Prevent triggering other click events
            toggleDeviceDetails(this);
        });
    });
});

function toggleChannelDropdown(dropdownElement) {
    const optionsDiv = dropdownElement.nextElementSibling;
    optionsDiv.style.display = (optionsDiv.style.display === 'none' || optionsDiv.style.display === '') ? 'block' : 'none';
}

function selectChannel(channelId, channelName, areaName, optionElement) {
    // Atualiza o nome do canal selecionado no dropdown
    const selectedChannelSpan = document.getElementById('selectedChannel-' + areaName);
    selectedChannelSpan.textContent = channelName;

    // Oculta o dropdown
    optionElement.parentElement.style.display = 'none';

    // Envia o canal selecionado para o backend
    fetch('/update_area_channel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `name=${encodeURIComponent(areaName)}&channel_id=${encodeURIComponent(channelId)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update channel');
        }

    })
}

function deleteInterrupt(interruptId) {
    if (confirm("Are you sure you want to delete this interrupt?")) {
        fetch(`/delete_interruption/${interruptId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Interrupt deleted successfully.");
                window.location.reload(); // Reload the page to update the list
            } else {
                alert("Error deleting interrupt: " + data.error);
            }
        })
        .catch(error => {
            console.error("Error during interrupt deletion:", error);
        });
    }
}


