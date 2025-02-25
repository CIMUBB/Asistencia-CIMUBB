document.addEventListener("DOMContentLoaded", function () {
    const notifyButton = document.getElementById("notify-button");
    const notifyBox = document.getElementById("notify-box");
    const closeNotify = document.getElementById("close-notify");
    const notifyList = document.getElementById("notify-list");
    const notifyCount = document.getElementById("notify-count"); 

    let socket = null;
    let unreadCount = 0;

    function loadStoredNotifications() {
        const storedNotifications = JSON.parse(localStorage.getItem("notifications")) || [];
        unreadCount = parseInt(localStorage.getItem("unreadCount")) || 0;
        notifyList.innerHTML = "";

        storedNotifications.reverse().forEach(msg => addNotification(msg));
        updateNotificationCounter();
    }

    function storeNotification(message) {
        let notifications = JSON.parse(localStorage.getItem("notifications")) || [];
        notifications.unshift(message);
        if (notifications.length > 10) {
            notifications.pop();
        }

        localStorage.setItem("notifications", JSON.stringify(notifications));

        unreadCount++;
        localStorage.setItem("unreadCount", unreadCount);
        updateNotificationCounter();
    }

    function addNotification(message) {
        const listItem = document.createElement("li");
        listItem.classList.add("notify-item");
        let iconClass = "fas fa-bell"; 

        if (message.toLowerCase().includes("salio")) {
            iconClass = "fas fa-sign-out-alt";
            listItem.classList.add("notify-salida");
        } else if (message.toLowerCase().includes("ingreso")) {
            iconClass = "fas fa-sign-in-alt";
            listItem.classList.add("notify-ingreso");
        }

        listItem.innerHTML = `<i class="${iconClass}"></i> ${message}`;
        notifyList.insertBefore(listItem, notifyList.firstChild);

        if (notifyList.children.length > 10) {
            notifyList.removeChild(notifyList.lastChild);
        }
    }

    function updateNotificationCounter() {
        if (unreadCount > 0) {
            notifyCount.textContent = unreadCount;
            notifyCount.style.display = "block";
        }
    }

    function connectWebSocket() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log("⚠️ Ya hay una conexión WebSocket activa.");
            return; // No conectar si ya está activo
        }

        socket = new WebSocket("ws://127.0.0.1:8000/ws/notify");

        socket.onopen = function () {
            console.log("✅ WebSocket conectado");
            setInterval(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send("ping");
                }
            }, 5000);
        };

        socket.onmessage = function (event) {
            console.log("📩 Notificación recibida:", event.data);
            const message = event.data;
            addNotification(message);
            storeNotification(message);
        };

        socket.onerror = function (error) {
            console.error("⚠️ WebSocket error:", error);
        };

        socket.onclose = function (event) {
            console.log(`🔴 WebSocket desconectado (code: ${event.code}). Reintentando en 3s...`);
            socket = null;
            setTimeout(connectWebSocket, 3000);
        };
    }

    // 🔌 Conectar WebSocket al cargar la página
    connectWebSocket();

    // 🔄 Cerrar WebSocket antes de recargar la página
    window.addEventListener("beforeunload", () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log("🔴 Cerrando WebSocket antes de salir...");
            socket.onclose = null;  // Evitar que reconecte automáticamente
            socket.close();
            navigator.sendBeacon("/ws/close");  // Avisar al servidor
        }
    });

    notifyButton.addEventListener("click", function () {
        notifyBox.classList.toggle("hidden");

        if (!notifyBox.classList.contains("hidden")) {
            unreadCount = 0;
            localStorage.setItem("unreadCount", unreadCount);
            updateNotificationCounter();
        }
    });

    closeNotify.addEventListener("click", function () {
        notifyBox.classList.add("hidden");
    });

    loadStoredNotifications();

    fetch("/api/dashboard")
        .then(response => response.json())
        .then(data => {
            if (data.notificaciones) {
                data.notificaciones.forEach(msg => {
                    addNotification(msg);
                    storeNotification(msg);
                });
            }
        })
        .catch(error => console.error("⚠️ Error cargando notificaciones:", error));
});
