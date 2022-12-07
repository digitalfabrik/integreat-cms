/**
 * If the content-edit-lock-data div exists, this file provides some functionality to periodically send heartbeats to the
 * server to acquire and keep the content editing look.
 * This file also registers an unload handler to quickly release the lock when not required anymore.
 */
import { showConfirmationPopupWithData } from "./confirmation-popups";
import { storeDraft } from "./forms/tinymce-init";
import { getCsrfToken } from "./utils/csrf-token";

let heartbeatInteval: NodeJS.Timer | null = null;
let unloadEventListener: (this: Window, ev: Event) => any | null = null;
let numHeartbeats = 0;

const sendMessage = async (url: string, payload: string): Promise<any> => {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: payload,
    });

    return response.json();
};

const sendTakeOverMessage = async (url: string, payload: string) => {
    await sendMessage(url, JSON.stringify({ key: payload, force: true }));
};

const sendHeartbeat = async (heartbeatData: HTMLElement) => {
    clearInterval(heartbeatInteval);

    const url = heartbeatData.getAttribute("data-heartbeat-url");
    const payload = heartbeatData.getAttribute("data-heartbeat-payload");
    const cancelUrl = heartbeatData.getAttribute("data-cancel-url");
    const result = await sendMessage(url, JSON.stringify({ key: payload, force: false }));
    if (!result.success) {
        // autosave changes if another user took control
        if (numHeartbeats !== 0) {
            storeDraft();
        }

        const popupTitleLocked = heartbeatData
            .getAttribute("data-popup-title-locked")
            .replace("{}", result.lockingUser);
        const popupTitleTakeover = heartbeatData
            .getAttribute("data-popup-title-takeover")
            .replace("{}", result.lockingUser);
        const popupSubject = heartbeatData.getAttribute("data-popup-subject");
        const popupText = heartbeatData.getAttribute("data-popup-text");

        showConfirmationPopupWithData(
            popupSubject,
            numHeartbeats === 0 ? popupTitleLocked : popupTitleTakeover,
            popupText,
            (_) =>
                sendTakeOverMessage(url, payload).then(() => {
                    window.removeEventListener("unload", unloadEventListener);
                    // window.location.reload() does not correctly work if the view is rendered after a post request, because then
                    // the browser tries to re-send the post request
                    /* eslint-disable-next-line no-self-assign */
                    window.location.href = window.location.href;
                }),
            (_) => {
                const escapeMeta = (raw: string) =>
                    raw.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
                window.location.href = escapeMeta(cancelUrl);
            }
        );
    } else {
        // Sends a heartbeat every 10 seconds
        const intervalLength = 10_000;
        heartbeatInteval = setInterval(() => sendHeartbeat(heartbeatData), intervalLength);
    }
    numHeartbeats += 1;
};

const setupHeartbeat = () => {
    const heartbeatData = document.getElementById("content-edit-lock-data");
    if (heartbeatData == null) {
        return;
    }

    // Immediately send a heartbeat to get unique edit access
    sendHeartbeat(heartbeatData);

    // On unload release the lock so the page is faster accessible again
    const lockReleaseUrl = heartbeatData.getAttribute("data-lock-release-url");
    const heartbeatPayload = heartbeatData.getAttribute("data-heartbeat-payload");
    unloadEventListener = () => sendMessage(lockReleaseUrl, heartbeatPayload);
    window.addEventListener("unload", unloadEventListener);
};

window.addEventListener("load", setupHeartbeat);
