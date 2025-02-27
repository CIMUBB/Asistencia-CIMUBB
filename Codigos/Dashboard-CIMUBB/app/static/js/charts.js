// Array de meses para reutilizar
const meses = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

// Gráfico de Utilización de Espacios
const motivosChartCtx = document
  .getElementById("motivos-chart")
  .getContext("2d");
const motivosChart = new Chart(motivosChartCtx, {
  type: "bar",
  data: {
    labels: [
      "asignatura",
      "asistencia tecnica",
      "investigacion",
      "practica profesional",
      "trabajo de titulo",
      "transferencia tecnologica",
    ],
    datasets: [
      {
        label: "Suma de Horas",
        data: Array(6).fill(0), // Inicialmente vacío
        backgroundColor: "rgba(255, 206, 86, 0.7)",
        borderColor: "rgba(255, 206, 86, 1)",
        borderWidth: 1,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});

// Gráfico de Evolución Mensual
const mensualChartCtx = document
  .getElementById("mensual-chart")
  .getContext("2d");
const mensualChart = new Chart(mensualChartCtx, {
  type: "line",
  data: {
    labels: meses, // Usar el array de meses definido
    datasets: [
      {
        label: "Cantidad de Horas",
        data: Array(12).fill(0), // Inicialmente vacío
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        borderColor: "rgba(75, 192, 192, 1)",
        borderWidth: 2,
        fill: true,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});

// Gráfico de Uso de Espacio por Día
const diaChartCtx = document.getElementById("dia-chart").getContext("2d");
const diaChart = new Chart(diaChartCtx, {
  type: "bar",
  data: {
    labels: ["lunes", "martes", "miércoles", "jueves", "viernes"], // No cambia
    datasets: [
      {
        label: "Horas Acumuladas",
        data: Array(5).fill(0), // Inicialmente vacío
        backgroundColor: "rgba(255, 99, 132, 0.7)",
        borderColor: "rgba(255, 99, 132, 1)",
        borderWidth: 1,
      },
    ],
  },
  options: {
    indexAxis: "y", // Hace que las barras sean horizontales
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
      },
    },
  },
});
