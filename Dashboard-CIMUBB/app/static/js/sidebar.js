document.addEventListener("DOMContentLoaded", () => {
  const btnFilter = document.querySelector(".btn-filter");
  const sidebarContainer = document.querySelector(".sidebar-container");
  const sidebar = document.querySelector(".sidebar");
  const mainContent = document.querySelector(".main-content");

  btnFilter.addEventListener("click", () => {
      // Alternar clases en el contenedor (no en el sidebar)
      sidebarContainer.classList.toggle("hidden");
      sidebar.classList.toggle("hidden");
      mainContent.classList.toggle("expanded");

      // Cambiar el ícono
      const icon = btnFilter.querySelector("i");
      icon.classList.toggle("fa-angle-double-left");
      icon.classList.toggle("fa-angle-double-right");
  });
});