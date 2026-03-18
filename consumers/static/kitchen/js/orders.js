import { initSocket } from "./socket.js";
import { updateWaitingTimes } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
    initSocket();
    setInterval(updateWaitingTimes, 1000);
});
