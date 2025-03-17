document.addEventListener("DOMContentLoaded", function () {
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
        const container = document.createElement("div");
        container.classList.add("select-container");
        const select = document.createElement("select");
        select.classList.add("select-column");
        select.multiple = true; // Allow multiple selections

        fetch("/get_free_nodes")
            .then(response => response.json())
            .then(nodes => {
                if (nodes.length === 0) {
                    buttonElement.remove(); // Remove the "+ Speaker" button if no speakers are available
                } else {
                    nodes.forEach(node => {
                        if (!usedZoneColumns.includes(node.name)) {
                            const option = document.createElement("option");
                            option.value = node.name;
                            option.textContent = node.name;
                            select.appendChild(option);
                        }
                    });
                    setTimeout(() => {
                        select.focus();
                        select.size = nodes.length; // Show all options
                    }, 100);
                }
            })
            .catch(error => console.error("Error fetching nodes:", error));

        container.appendChild(select);
        buttonElement.replaceWith(container);

        select.addEventListener("change", function (event) {
            event.preventDefault();
            addZoneColumns(select, buttonElement);
        });
    }

    function addZoneColumns(selectElement, buttonElement) {
        const selectedOptions = Array.from(selectElement.selectedOptions);
        if (selectedOptions.length === 0) return;
        const zoneName = selectElement.closest(".zone-box").querySelector("h3").textContent.trim();
        const zoneContainer = selectElement.closest(".column-list");

        selectedOptions.forEach(option => {
            const columnItem = document.createElement("div");
            columnItem.classList.add("column-item");
            columnItem.innerHTML = `
                <span>${option.value}</span>
                <button class="delete-column-button">
                    <i class="fa-solid fa-trash" style="color: black;"></i>
                </button>
            `;
            columnItem.dataset.column = option.value;
            columnItem.dataset.zone = zoneName;
            columnItem.querySelector(".delete-column-button").addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                removeZoneColumn(columnItem);
            });
            zoneContainer.insertBefore(columnItem, selectElement.parentElement);
            usedZoneColumns.push(option.value); // Add to used columns
        });

        selectElement.parentElement.replaceWith(buttonElement);

        const selectedColumns = selectedOptions.map(option => option.value);
        fetch("/add_columns_to_zone", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ zone_name: zoneName, column_names: selectedColumns })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
                selectedColumns.forEach(column => {
                    const columnItem = zoneContainer.querySelector(`.column-item[data-column="${column}"]`);
                    if (columnItem) columnItem.remove();
                    usedZoneColumns = usedZoneColumns.filter(name => name !== column); // Remove from used columns
                });
            }
        })
        .catch(error => console.error("Error adding speakers:", error));
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
                usedZoneColumns = usedZoneColumns.filter(name => name !== columnName); // Remove from used columns
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
});

