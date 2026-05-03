export function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case "ordering":
            return "primary";
        case "preparing":
            return "warning text-dark";
        case "ready":
            return "success";
        default:
            return "secondary";
    }
}

export function updateWaitingTimes() {
    document.querySelectorAll(".waiting-time").forEach(span => {
        const createdAt = new Date(span.dataset.createdAt);
        const diff = Math.floor((new Date() - createdAt) / 1000);
        span.textContent = `${Math.floor(diff / 60)}m ${diff % 60}s`;
    });
}
