/**
 * If the content-edit-lock-data div exists, this file provides some functionality to periodically send heartbeats to the
 * server to acquire and keep the content editing look.
 * This file also registers an unload handler to quickly release the lock when not required anymore.
 */
import { showConfirmationPopupWithData } from "./confirmation-popups";
import { storeDraft } from "./forms/tinymce-init";
import { getCsrfToken } from "./utils/csrf-token";

window.addEventListener("load", setup_heartbeat);

let heartbeat_interval: NodeJS.Timer | null = null;
let unload_event_listener: (this: Window, ev: Event) => any | null = null;
let num_heartbeats = 0;

function setup_heartbeat() {
    const heartbeat_data = document.getElementById("content-edit-lock-data");
    if (heartbeat_data == null) {
        return;
    }

    // Immediately send a heartbeat to get unique edit access
    send_heartbeat(heartbeat_data);

    // On unload release the lock so the page is faster accessible again
    const lock_release_url = heartbeat_data.getAttribute("data-lock-release-url");
    const heartbeat_payload = heartbeat_data.getAttribute("data-heartbeat-payload");
    unload_event_listener = () => send_message(lock_release_url, heartbeat_payload);
    window.addEventListener("unload", unload_event_listener);
}

async function send_heartbeat(heartbeat_data: HTMLElement) {
    clearInterval(heartbeat_interval);

    const url = heartbeat_data.getAttribute("data-heartbeat-url");
    const payload = heartbeat_data.getAttribute("data-heartbeat-payload");
    const cancel_url = heartbeat_data.getAttribute("data-cancel-url");
    const result = await send_message(url, JSON.stringify({ key: payload, force: false }));
    if (!result.success) {
        // autosave changes if another user took control
        if (num_heartbeats != 0) {
            storeDraft();
        }

        const popup_title_locked = heartbeat_data
            .getAttribute("data-popup-title-locked")
            .replace("{}", result.lockingUser);
        const popup_title_takeover = heartbeat_data
            .getAttribute("data-popup-title-takeover")
            .replace("{}", result.lockingUser);
        const popup_subject = heartbeat_data.getAttribute("data-popup-subject");
        const popup_text = heartbeat_data.getAttribute("data-popup-text");

        showConfirmationPopupWithData(
            popup_subject,
            num_heartbeats == 0 ? popup_title_locked : popup_title_takeover,
            popup_text,
            (_) =>
                send_take_over_message(url, payload).then(() => {
                    window.removeEventListener("unload", unload_event_listener);
                    // window.location.reload() does not correctly work if the view is rendered after a post request, because then
                    // the browser tries to re-send the post request
                    window.location.href = window.location.href;
                }),
            (_) => (window.location.href = cancel_url)
        );
    } else {
        // Sends a heartbeat every 10 seconds
        heartbeat_interval = setInterval(() => send_heartbeat(heartbeat_data), 10_000);
    }
    num_heartbeats += 1;
}

async function send_take_over_message(url: string, payload: string) {
    await send_message(url, JSON.stringify({ key: payload, force: true }));
}

async function send_message(url: string, payload: string): Promise<any> {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: payload,
    });

    return await response.json();
}
