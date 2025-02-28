// Función para obtener los datos filtrados desde el backend
async function fetchFilteredData() {
  const year = document.getElementById("year-filter").value;
  const month = document.getElementById("month-filter").value;
  const day = document.getElementById("day-filter").value;
  const motivo = document.getElementById("motivo-filter").value;
  const rut = document.getElementById("rut-filter").value;

  // Construir la URL con los parámetros de filtro
  let url = `/api/dashboard?year=${year}`;
  if (month !== "all") url += `&month=${month}`;
  if (day !== "") url += `&day=${day}`;
  if (motivo !== "all") url += `&motivo=${motivo}`;
  if (rut !== "") url += `&rut=${rut}`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    renderTable(data.registros); // Renderizar la tabla con los datos recibidos
    updateStats(data.registros); // Actualizar estadísticas
    paginateTable(5);
    updateCharts(data.registros);
  } catch (error) {
    console.error("Error al obtener los datos:", error);
  }
}

// Función para renderizar la tabla con los datos
function renderTable(data) {
  const tbody = document.getElementById("details-body");
  const fragment = document.createDocumentFragment(); // Crea un fragmento

  data.forEach((item) => {
    // Descomponer la fecha manualmente para evitar problemas de zona horaria
    const [year, month, day] = item.fecha.split("-");
    const fecha = `${day}-${month}-${year}`;
    const verificado = item.verificado;

    // Formatear hora a hh:mm
    const horaIngreso = item.hora_ingreso
      ? item.hora_ingreso.slice(0, 5)
      : "N/A";
    const horaSalida =
      item.hora_salida && item.hora_salida !== "None"
        ? item.hora_salida.slice(0, 5)
        : "N/A";

    // Formatear motivo a Start Case
    const motivo = item.motivo
      ? item.motivo
          .split("_")
          .map(
            (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
          )
          .join(" ")
      : "N/A";

    // Agregar hipervínculo al RUT
    // const rutLink = `<a href="#" class="rut-link" data-rut="${item.rut}">${item.rut}</a>`;
    const rutLink = `<a href="/profile?rut=${encodeURIComponent(item.rut)}" class="rut-link">${item.rut}</a>`;

    // Crear fila como nodo
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${fecha}</td>
      <td>${motivo}</td>
      <td>${rutLink}</td>
      <td>${verificado}</td>
      <td>${horaIngreso}</td>
      <td>${horaSalida}</td>
    `;

    // Añadir fila al fragmento
    fragment.appendChild(row);
  });

  // Limpiar tbody y añadir el fragmento en una sola operación
  tbody.innerHTML = "";
  tbody.appendChild(fragment);
}

function updateStats(data) {
  let totalHoras = 0;

  // Crear un conjunto para contar usuarios únicos
  const usuariosUnicos = new Set();

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

    // Agregar el RUT al conjunto de usuarios únicos
    usuariosUnicos.add(item.rut);
  });

  // Mostrar los resultados en la página
  document.getElementById("total-horas").textContent = totalHoras.toFixed(2);
  document.getElementById("total-usuarios").textContent =
    usuariosUnicos.size;
}

function updateCharts(data) {
  // Función para obtener el día de la semana
  function getDayOfWeek(fecha) {
    const diasSemana = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
    const date = new Date(fecha);
    return diasSemana[date.getUTCDay()]; // Devuelve el nombre del día en español
  }

  // Etiquetas internas (sin acentos, en minúsculas)
  const motivosLabels = [
    "asignatura",
    "asistencia tecnica",
    "investigacion",
    "practica profesional",
    "trabajo de titulo",
    "transferencia tecnologica",
  ];

  const mesesLabels = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
  ];

  const diasSemanaLabels = ["lunes", "martes", "miércoles", "jueves", "viernes"];

  // Etiquetas para visualización (formateadas con Start Case y acentos)
  const motivosDisplayLabels = [
    "Asignatura",
    "Asistencia Técnica",
    "Investigación",
    "Práctica Profesional",
    "Trabajo de Título",
    "Transferencia Tecnológica",
  ];

  const mesesDisplayLabels = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
  ];

  const diasSemanaDisplayLabels = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"];

  // Datos iniciales
  const motivosData = Array(motivosLabels.length).fill(0);
  const mensualData = Array(mesesLabels.length).fill(0);
  const diaData = Array(diasSemanaLabels.length).fill(0);

  // Procesar los datos
  data.forEach((item) => {
    if (item.hora_ingreso && item.hora_salida && item.hora_salida !== "None") {
      // Calcular la diferencia de horas
      const horaIngreso = new Date(`1970-01-01T${item.hora_ingreso}`);
      const horaSalida = new Date(`1970-01-01T${item.hora_salida}`);
      const diferenciaHoras = (horaSalida - horaIngreso) / (1000 * 60 * 60);

      // Procesar datos por motivo
      const motivoIndex = motivosLabels.indexOf(item.motivo);
      if (motivoIndex >= 0) {
        motivosData[motivoIndex] += diferenciaHoras;
      }

      // Procesar datos por mes
      const monthIndex = parseInt(item.fecha.split("-")[1], 10) - 1;
      if (monthIndex >= 0 && monthIndex < 12) {
        mensualData[monthIndex] += diferenciaHoras;
      }

      // Procesar datos por día
      const diaSemana = getDayOfWeek(item.fecha);
      const dayIndex = diasSemanaLabels.indexOf(diaSemana.toLowerCase());
      if (dayIndex >= 0) {
        diaData[dayIndex] += diferenciaHoras;
      }
    }
  });

  // Actualizar datos de los gráficos
  motivosChart.data.labels = motivosDisplayLabels; // Etiquetas visuales
  motivosChart.data.datasets[0].data = motivosData;
  motivosChart.update();

  mensualChart.data.labels = mesesDisplayLabels; // Etiquetas visuales
  mensualChart.data.datasets[0].data = mensualData;
  mensualChart.update();

  diaChart.data.labels = diasSemanaDisplayLabels; // Etiquetas visuales
  diaChart.data.datasets[0].data = diaData;
  diaChart.update();
}


function resetFilters() {
  const currentYear = new Date().getFullYear();

  document.getElementById("year-filter").value = currentYear;
  document.getElementById("month-filter").value = "all";
  document.getElementById("day-filter").value = "";
  document.getElementById("motivo-filter").value = "all";
  document.getElementById("rut-filter").value = "";

  fetchFilteredData();
}

// Escuchar los clics en los enlaces de la clase "rut-link"
document.addEventListener("click", (event) => {
  const target = event.target;

  if (target.classList.contains("rut-link")) {
    // Verifica si tiene el atributo href
    const url = target.getAttribute("href");

    if (url) {
      // Permitir la redirección normal
      return;
    }

    // Si no tiene href, entonces es el caso donde filtras los datos
    event.preventDefault(); 

    const rut = target.getAttribute("data-rut");

    if (rut) {
      document.getElementById("rut-filter").value = rut;
      fetchFilteredData();
    }
  }
});


// Vincular los eventos de los filtros para actualizar los datos
document
  .getElementById("year-filter")
  .addEventListener("change", fetchFilteredData);
document
  .getElementById("month-filter")
  .addEventListener("change", fetchFilteredData);
document
  .getElementById("day-filter")
  .addEventListener("change", fetchFilteredData);
document
  .getElementById("motivo-filter")
  .addEventListener("change", fetchFilteredData);
document
  .getElementById("rut-filter")
  .addEventListener("input", fetchFilteredData);
// Cargar los datos al inicio
document.addEventListener("DOMContentLoaded", fetchFilteredData);
