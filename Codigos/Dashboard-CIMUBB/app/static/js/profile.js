document.addEventListener("DOMContentLoaded", function () {
    // Obtener los datos del script con ID 'profile-data'
    const profileDataElement = document.getElementById("profile-data");
    if (!profileDataElement) {
        console.error("No se encontró el elemento con ID 'profile-data'");
        return;
    }

    let data;
    try {
        data = JSON.parse(profileDataElement.textContent);
    } catch (error) {
        console.error("Error al parsear los datos de perfil:", error);
        return;
    }

    updateStats(data);

    const recordsPerPage = 5;
    let currentPage = 1;
    const totalPages = Math.ceil(data.length / recordsPerPage);

    function renderProfileTable(page) {
        const tbody = document.getElementById("profile-details-body");
        tbody.innerHTML = ""; // Limpiar tabla antes de renderizar

        // Calcular el índice de inicio y fin de la página actual
        const startIndex = (page - 1) * recordsPerPage;
        const endIndex = startIndex + recordsPerPage;
        const pageData = data.slice(startIndex, endIndex);

        // Agregar filas con los datos
        pageData.forEach((item) => {
            const [year, month, day] = item.fecha.split("-");
            const fecha = `${day}-${month}-${year}`;

            const motivo = item.motivo
                ? item.motivo
                      .split("_")
                      .map(
                          (word) =>
                              word.charAt(0).toUpperCase() +
                              word.slice(1).toLowerCase()
                      )
                      .join(" ")
                : "N/A";

            const horaIngreso = item.hora_ingreso
                ? item.hora_ingreso.slice(0, 5)
                : "N/A";
            const horaSalida =
                item.hora_salida && item.hora_salida !== "None"
                    ? item.hora_salida.slice(0, 5)
                    : "N/A";

            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${fecha}</td>
                <td>${motivo}</td>
                <td>${horaIngreso}</td>
                <td>${horaSalida}</td>
            `;

            tbody.appendChild(row);
        });

        // Rellenar filas vacías si hay menos de 5 registros en la página actual
        for (let i = pageData.length; i < recordsPerPage; i++) {
            const emptyRow = document.createElement("tr");
            emptyRow.innerHTML = `
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
            `;
            tbody.appendChild(emptyRow);
        }

        renderPagination();
    }

    function renderPagination() {
        const paginationContainer = document.getElementById("profile-pagination-container");
        paginationContainer.innerHTML = "";

        // Botón "Primera Página"
        const firstButton = document.createElement("button");
        firstButton.textContent = "Inicio";
        firstButton.classList.add("pagination-button");
        firstButton.disabled = currentPage === 1;
        firstButton.addEventListener("click", () => changePage(1));
        paginationContainer.appendChild(firstButton);

        // Botón "Anterior"
        const prevButton = document.createElement("button");
        prevButton.textContent = "Anterior";
        prevButton.classList.add("pagination-button");
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener("click", () => changePage(currentPage - 1));
        paginationContainer.appendChild(prevButton);

        // Input para escribir página específica
        const pageInput = document.createElement("input");
        pageInput.type = "number";
        pageInput.classList.add("pagination-input");
        pageInput.min = 1;
        pageInput.max = totalPages;
        pageInput.value = currentPage;
        pageInput.addEventListener("change", () => {
            let page = parseInt(pageInput.value);
            if (page >= 1 && page <= totalPages) {
                changePage(page);
            } else {
                pageInput.value = currentPage;
            }
        });
        paginationContainer.appendChild(pageInput);

        // Botón "Siguiente"
        const nextButton = document.createElement("button");
        nextButton.textContent = "Siguiente";
        nextButton.classList.add("pagination-button");
        nextButton.disabled = currentPage === totalPages;
        nextButton.addEventListener("click", () => changePage(currentPage + 1));
        paginationContainer.appendChild(nextButton);

        // Botón "Última Página"
        const lastButton = document.createElement("button");
        lastButton.textContent = "Final";
        lastButton.classList.add("pagination-button");
        lastButton.disabled = currentPage === totalPages;
        lastButton.addEventListener("click", () => changePage(totalPages));
        paginationContainer.appendChild(lastButton);
    }

    function changePage(page) {
        if (page >= 1 && page <= totalPages) {
            currentPage = page;
            renderProfileTable(currentPage);
        }
    }

    // Renderizar la primera página al cargar
    renderProfileTable(currentPage);
});

function updateStats(data) {
    let horasPorDia = { 1: [], 2: [], 3: [], 4: [], 5: [] }; // Lunes a Viernes
    let totalHorasPorDia = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    let conteoDias = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };

    data.forEach((item) => {
        if (item.hora_salida && item.hora_salida !== "None") {
            const fecha = item.fecha;
            const diaSemana = new Date(fecha).getDay();

            if (diaSemana >= 1 && diaSemana <= 5) {
                const horaIngreso = new Date(`1970-01-01T${item.hora_ingreso}`);
                const horaSalida = new Date(`1970-01-01T${item.hora_salida}`);
                const diferenciaHoras = (horaSalida - horaIngreso) / (1000 * 60 * 60);

                horasPorDia[diaSemana].push(diferenciaHoras);
                totalHorasPorDia[diaSemana] += diferenciaHoras;
                conteoDias[diaSemana]++;
            }
        }
    });

    let promedioHorasPorDia = {};
    for (let i = 1; i <= 5; i++) {
        promedioHorasPorDia[i] = conteoDias[i] > 0 ? totalHorasPorDia[i] / conteoDias[i] : 0;
    }

    renderStatsTable(promedioHorasPorDia);
    renderStatsChart(promedioHorasPorDia);
    let totalHoras = 0;
    // Recorrer los datos para calcular las horas y contar los usuarios
    data.forEach((item) => {
      // Ignorar registros donde la hora_salida es null o None
      if (item.hora_salida && item.hora_salida !== "None") {
        // Convertir las horas a objetos Date
        const horaIngreso = new Date(`1970-01-01T${item.hora_ingreso}`);
        const horaSalida = new Date(`1970-01-01T${item.hora_salida}`);
  
        // Calcular la diferencia en milisegundos y convertir a horas
        const diferenciaHoras = (horaSalida - horaIngreso) / (1000 * 60 * 60);
  
        // Sumar la diferencia al total de horas
        totalHoras += diferenciaHoras;
      }
    });
  
    // Mostrar los resultados en la página
    document.getElementById("total-horas").textContent = totalHoras.toFixed(2);
}
function renderStatsTable(promedioHorasPorDia) {
    const tableContainer = document.getElementById("average-hours-table");
    tableContainer.innerHTML = `
        <table class="average-table">
            <thead>
                <tr><th>Día</th><th>Promedio de Horas</th></tr>
            </thead>
            <tbody>
                <tr><td>Lunes</td><td>${promedioHorasPorDia[1].toFixed(2)}</td></tr>
                <tr><td>Martes</td><td>${promedioHorasPorDia[2].toFixed(2)}</td></tr>
                <tr><td>Miércoles</td><td>${promedioHorasPorDia[3].toFixed(2)}</td></tr>
                <tr><td>Jueves</td><td>${promedioHorasPorDia[4].toFixed(2)}</td></tr>
                <tr><td>Viernes</td><td>${promedioHorasPorDia[5].toFixed(2)}</td></tr>
            </tbody>
        </table>
    `;
}

function renderStatsChart(promedioHorasPorDia) {
    const ctx = document.getElementById("averageHoursChart").getContext("2d");
    if (window.myChart) window.myChart.destroy();

    window.myChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
            datasets: [{ label: "Horas Promedio", data: Object.values(promedioHorasPorDia) }]
        }
    });
}
