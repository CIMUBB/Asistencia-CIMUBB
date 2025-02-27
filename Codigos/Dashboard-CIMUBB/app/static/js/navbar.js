document.addEventListener("DOMContentLoaded", function () {
    // Manejo del menú hamburguesa
    const hamburger = document.querySelector(".hamburger");
    const menu = document.querySelector("#navbar-menu");

    hamburger.addEventListener("click", function () {
        const expanded = this.getAttribute("aria-expanded") === "true";
        this.setAttribute("aria-expanded", !expanded);
        menu.classList.toggle("active");
    });

    // Manejo de la búsqueda por RUT
    const searchContainer = document.querySelector(".search-container");
    const searchBtn = document.getElementById("search-btn");
    const searchInput = document.getElementById("search-input");
    const searchForm = document.getElementById("search-form");

    // Contenedor para mostrar errores
    const errorContainer = document.createElement("div");
    errorContainer.id = "error-message";
    errorContainer.style.color = "red";
    errorContainer.style.fontSize = "14px";
    errorContainer.style.fontFamily = "'Montserrat', sans-serif";
    errorContainer.style.marginTop = "-5px"

    searchContainer.insertAdjacentElement("afterend", errorContainer);


    // Mostrar input de búsqueda al hacer clic en el botón
    searchBtn.addEventListener("click", function () {
        searchContainer.classList.add("active");
        searchInput.focus();
    });

    // Cerrar la búsqueda si se hace clic fuera del contenedor
    document.addEventListener("click", function (event) {
        if (!searchContainer.contains(event.target)) {
            searchContainer.classList.remove("active");
        }
    });

    // Manejo de la validación y solicitud al backend
    searchForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Evita recargar la página
        errorContainer.textContent = ""; // Borra errores previos

        const rut = searchInput.value.trim();
        if (!rut) {
            errorContainer.textContent = "El campo RUT no puede estar vacío.";
            return;
        }

        fetch(`/profile?rut=${encodeURIComponent(rut)}`, {
            method: "GET",
            headers: { "Accept": "application/json" },
        })
        .then(async (response) => {
            const data = await response.json();
            if (!response.ok) {
                // Si la respuesta contiene errores, los mostramos
                if (data.errors) {
                    errorContainer.textContent = data.errors.map(err => err.message).join(" ");
                } else {
                    errorContainer.textContent = "Ocurrió un error inesperado.";
                }
            } else {
                // Si no hay errores, redirige al perfil
                window.location.href = `/profile?rut=${encodeURIComponent(rut)}`;
            }
        })
        .catch((error) => {
            console.error("Error al buscar el perfil:", error);
            errorContainer.textContent = "Error al procesar la solicitud.";
        });
    });
});
