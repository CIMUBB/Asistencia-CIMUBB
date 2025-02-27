document.addEventListener("DOMContentLoaded", function () {
  paginateTable(5); // Muestra 5 registros por página
});

function paginateTable(rowsPerPage) {
  const tbody = document.getElementById("details-body");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const paginationContainer = document.getElementById("pagination-container");

  let currentPage = 1;
  const totalPages = Math.ceil(rows.length / rowsPerPage);

  function renderTable(page) {
    tbody.innerHTML = "";
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    rows.slice(start, end).forEach((row) => tbody.appendChild(row));
  }

  function renderPagination() {
    paginationContainer.innerHTML = "";

    // Botón "Primera Página"
    const firstButton = document.createElement("button");
    firstButton.textContent = "Inicio";
    firstButton.disabled = currentPage === 1;
    firstButton.addEventListener("click", () => {
      currentPage = 1;
      renderTable(currentPage);
      renderPagination();
    });
    paginationContainer.appendChild(firstButton);

    // Botón "Anterior"
    const prevButton = document.createElement("button");
    prevButton.textContent = "Anterior";
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener("click", () => {
      currentPage = Math.max(1, currentPage - 1);
      renderTable(currentPage);
      renderPagination();
    });
    paginationContainer.appendChild(prevButton);

    // Input para escribir página específica
    const pageInput = document.createElement("input");
    pageInput.type = "number";
    pageInput.min = 1;
    pageInput.max = totalPages;
    pageInput.value = currentPage;
    pageInput.addEventListener("change", () => {
      const page = parseInt(pageInput.value);
      if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderTable(currentPage);
        renderPagination();
      } else {
        pageInput.value = currentPage;
      }
    });
    paginationContainer.appendChild(pageInput);

    // Botón "Siguiente"
    const nextButton = document.createElement("button");
    nextButton.textContent = "Siguiente";
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener("click", () => {
      currentPage = Math.min(totalPages, currentPage + 1);
      renderTable(currentPage);
      renderPagination();
    });
    paginationContainer.appendChild(nextButton);

    // Botón "Última Página"
    const lastButton = document.createElement("button");
    lastButton.textContent = "Final";
    lastButton.disabled = currentPage === totalPages;
    lastButton.addEventListener("click", () => {
      currentPage = totalPages;
      renderTable(currentPage);
      renderPagination();
    });
    paginationContainer.appendChild(lastButton);
  }

  renderTable(currentPage);
  renderPagination();
}