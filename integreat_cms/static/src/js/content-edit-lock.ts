/**
 * This file periodically sends a request to the server if the user is editing some content
 */
import { getCsrfToken } from "./utils/csrf-token";

window.addEventListener("load", () => setup_heartbeat());

function setup_heartbeat() {
    const heartbeat_data = document.getElementById("content-edit-lock-data");
    if (heartbeat_data == null) {
        return;
    }

    const heartbeat_url = heartbeat_data.getAttribute("data-heartbeat-url");
    const lock_release_url = heartbeat_data.getAttribute("data-lock-release-url");
    const heartbeat_payload = heartbeat_data.getAttribute("data-heartbeat-payload");
    setInterval(() => send_message(heartbeat_url, heartbeat_payload), 10_000);
    // Immediately send a heartbeat to get unique edit access
    send_message(heartbeat_url, heartbeat_payload);

    // On unload release the lock so the page is faster accessible again
    window.addEventListener("unload", () => send_message(lock_release_url, heartbeat_payload));
}

async function send_message(url: string, payload: string) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: payload,
    });

    const json = await response.json();
    if (!json.success) {
        console.warn("Failed heartbeat with payload " + payload);
    }
}