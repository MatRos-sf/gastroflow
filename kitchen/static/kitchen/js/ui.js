import { sendSocketMessage } from "./socket.js";
import { getStatusClass } from "./utils.js";

export function addOrderToView(order) {
    if (document.getElementById(`order-${order.id}`)) return;

    let itemsHtml = order.order_items.map(item => {
        const doneClass = item.is_done ? "text-decoration-line-through text-muted" : "";
        return `
            <li class="list-group-item ${doneClass}"
                id="order-${order.id}-item-${item.id}"
                onclick="window.toggleItemDone(${order.id}, ${item.id}, '${order.sender}')">
                ${item.name_snapshot} ×${item.quantity}
                ${item.note ? `<small class="text-muted">(${item.note})</small>` : ""}
            </li>
        `;
    }).join("");

    const el = document.createElement("div");
    el.id = `order-${order.id}`;
    el.className = "card mb-3 shadow-sm order-card";

    el.innerHTML = `
        <div class="card-header d-flex justify-content-between">
            <h5>Order #${order.id} @${order.sender}</h5>
            <span id="status-${order.id}" class="badge bg-${getStatusClass(order.status)}">
                ${order.status}
            </span>
        </div>
        <div class="card-body">
            <p><strong>Stół:</strong> ${order.table}</p>
            <p>
                <strong>Czas oczekiwania:</strong>
                <span class="waiting-time" data-created-at="${order.created_at}">0m 0s</span>
            </p>
            <ul class="list-group mb-3">${itemsHtml}</ul>
            <div class="d-flex gap-2">
                <button class="btn btn-warning"
                    onclick="window.changeStatus(${order.id}, 'preparing')">
                    Preparing
                </button>
                <button class="btn btn-success"
                    onclick="window.changeStatus(${order.id}, 'ready')">
                    Ready
                </button>
            </div>
        </div>
    `;

    document.getElementById("orders-container").append(el);
}

export function updateOrderStatus(orderId, status) {
    const span = document.getElementById(`status-${orderId}`);
    if (!span) return;

    span.innerText = status;
    span.className = `badge bg-${getStatusClass(status)}`;
}

export function removeOrder(orderId) {
    document.getElementById(`order-${orderId}`)?.remove();
}

/* global functions for onclick */
window.changeStatus = (orderId, status) => {
    sendSocketMessage({ action: status, order_id: orderId });
};

window.toggleItemDone = (orderId, itemId, username) => {
    const el = document.getElementById(`order-${orderId}-item-${itemId}`);
    el.classList.toggle("text-decoration-line-through");
    el.classList.toggle("text-muted");

    sendSocketMessage({
        action: "item_done",
        order_id: orderId,
        item_id: itemId,
        username
    });
};
