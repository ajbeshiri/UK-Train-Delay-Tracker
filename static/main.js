// Open station JSON and parse data
async function getAllStations() {
    try {
        const response = await fetch('uk-train-stations.json');

        if (!response.ok) {
            throw new Error(`HTTP error. Status: ${response.status}`);
        }

        const stations = await response.json();
        return stations;
    } catch (error) {
        console.error('Failed to fetch station data:', error);
    }
}

function searchStation() {
    const input = document.getElementById("stationSearch");
    const filter = input.value.toUpperCase();

    const table = document.getElementById("station-table-container");
    const rows = table.querySelectorAll("tbody tr");

    rows.forEach(row => {
        const name = row.cells[1].textContent.toUpperCase();

        if (name.includes(filter)) {
            row.style.display = "";
        }
        else {
            row.style.display = "none";
        }
    });
}

function getSelectedStationRow() {
    const selectedRow = document.querySelector("#station-table tbody tr.selected");

    if(!selectedRow) {
        return null;
    }

    return selectedRow.cells[0].textContent;
}

async function getStationData() {
    const station = getSelectedStationRow();
    const errorMessage = document.querySelector(".error-message-txt");
    errorMessage.style.display = "none";

    if (!station) {
        errorMessage.textContent = "You have not selected a station. Please select a station from the list above.";
        errorMessage.style.display = "block";
        return;
    }

    try {
        const response = await fetch(`/api/v1/delays/${station}`);

        if (!response.ok) {
            errorMessage.textContent = "An error has occured. Please try again later.";
            errorMessage.style.display = "block";
            return;
        }

        const result = await response.json();

        if (!result.success) {
            errorMessage.textContent = result.reason ?? "An error has occurred. Please try again later.";
            errorMessage.style.display = "block";
            return;
        }

        const stationData = result.response;

        const stationName = document.getElementById("station-name");
        const updatedTime = document.getElementById("updated-time");
        const tableBody = document.getElementById("services-table");

        stationName.textContent =  `${stationData.station.name} (${stationData.station.code})`;
        const lastUpdated = new Date(stationData.updated_at).toLocaleString();
        updatedTime.textContent = lastUpdated;
        tableBody.innerHTML = '';

        stationData.services.forEach(service => {
            let status = {text: "On time", className: "on-time"};

            if(service.cancelled) {
                status = {text: "Cancelled", className: "cancelled"};
            }
            else if(service.delay_minutes > 0) {
                status = {text: `${service.delay_minutes} min${service.delay_minutes > 1 ? 's' : ''} late`, className: "delayed"};
            }
            else if(service.delay_minutes < 0) {
                status = {text: `${Math.abs(service.delay_minutes)} min${Math.abs(service.delay_minutes) > 1 ? 's' : ''} early`, className: "early"};
            }

            const row = document.createElement("tr");
            const displayedTime = service.actual_time ?? service.expected_time ?? "N/A";
            const scheduledTime = service.scheduled_time ?? "N/A";

            row.innerHTML = `
                <td>${service.operator}</td>
                <td>${service.origin}</td>
                <td>${service.destination}</td>
                <td>${service.platform ?? "N/A"}</td>
                <td>${scheduledTime}</td>
                <td>${displayedTime}</td>
                <td>
                    <div class="status ${status.className}">
                        ${status.text}
                    </div>
                    ${service.reason ? `<div class="reason">${service.reason}</div>` : ""}
                </td>
            `;

            tableBody.appendChild(row);
        });

    } catch (error) {
        errorMessage.textContent = "An error has occured. Please try again later.";
        errorMessage.style.display = "block";
        return;
    }
}

getAllStations().then(stations => {
    if (!stations) {
        return;
    }
    
    const stationTable = document.querySelector("#station-table-container tbody");

    stations.forEach((station) => {
        const row = document.createElement("tr");

        const codeCell = document.createElement("td");
        codeCell.textContent = station.station_code;

        const nameCell = document.createElement("td");
        nameCell.textContent = station.station_name;

        row.appendChild(codeCell);
        row.appendChild(nameCell);

        stationTable.appendChild(row);
    });
});

const table = document.getElementById("station-table");

table.addEventListener('click', (event) => {
    const row = event.target.closest('tr');
    if(!row || row.parentElement.tagName !== 'TBODY') return;

    const selectedRows = document.querySelectorAll("#station-table tbody tr.selected");

    if(selectedRows.length >= 1 && !row.classList.contains('selected')) {
        const selected = document.querySelector(".selected");
        if(selected) {
            selected.classList.remove('selected');
        }
    }

    row.classList.toggle('selected');
});