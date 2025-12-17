import {
    addOrderToView,
    updateOrderStatus,
    removeOrder
} from "./ui.js";

const ordersContainer = document.getElementById("orders-container");
const pingInterval = 30000;

let kitchenSocket = null;

export function initSocket() {
    kitchenSocket = new WebSocket(
        "ws://" + window.location.host + "/ws/kitchen/orders/"
    );

    kitchenSocket.onopen = () => {
        console.log("WebSocket connected");
        setupPing();
    };

    kitchenSocket.onmessage = handleMessage;

    kitchenSocket.onclose = () => {
        console.error("Kitchen socket closed");
    };
}

function setupPing() {
    setInterval(() => {
        if (kitchenSocket.readyState === WebSocket.OPEN) {
            kitchenSocket.send(JSON.stringify({ action: "ping" }));
        }
    }, pingInterval);
}

function handleMessage(e) {
    const data = JSON.parse(e.data);
    console.log("Message received:", data);

    if (data.type === "initial_orders") {
        ordersContainer.innerHTML = "";
        data.orders.forEach(addOrderToView);

    } else if (data.type === "new_order") {
        addOrderToView(data.order);
        playSound();

    } else if (data.type === "order_status_update") {
        if (data.new_status.toLowerCase() === "ready") {
            removeOrder(data.order_id);
        } else {
            updateOrderStatus(data.order_id, data.new_status);
        }
    }
}

export function sendSocketMessage(payload) {
    kitchenSocket.send(JSON.stringify(payload));
}

function playSound() {
    const sound = document.getElementById("notification-sound");
    if (sound) {
        sound.play().catch(() => {});
    }
}
