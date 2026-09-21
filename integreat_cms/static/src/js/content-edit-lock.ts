/**
 * If the content-edit-lock-data div exists, this file provides some functionality to periodically send heartbeats to the
 * server to acquire and keep the content editing look.
 * This file also registers an unload handler to quickly release the lock when not required anymore.
 */
import { showConfirmationPopupWithData } from "./utils/confirmation-popup";
import { storeDraft } from "./forms/tinymce-init";
import { getCsrfToken } from "./utils/csrf-token";
import { showReportBanners } from "./utils/mt-report-banner";

let heartbeatInterval: ReturnType<typeof setTimeout> | null = null;
let unloadEventListener: (this: Window, ev: Event) => any | null = null;
let numHeartbeats = 0;
let isMachineTranslationLockShowing = false;
let hasActiveChildTranslation = false;

/**
 * Shows/hides the "this page is translating into other languages" line
 * based on the heartbeat's `activeChildTranslationTaskId`, and shows the
 * outcome banner once a previously-active one is no longer running. Reuses
 * the heartbeat's own request/interval rather than a dedicated poll, since
 * this and the human edit-lock check both need the same "is anything still
 * going on for this page" answer on the same cadence.
 *
 * @param heartbeatData The heartbeat data element (for the report url)
 * @param activeTaskId The task id from the latest heartbeat response, if any
 */
const updateChildTranslationProgress = (heartbeatData: HTMLElement, activeTaskId: string | null) => {
    const inProgressLine = document.getElementById("mt-source-in-progress-line");
    if (activeTaskId) {
        hasActiveChildTranslation = true;
        inProgressLine?.classList.remove("hidden");
        return;
    }
    if (hasActiveChildTranslation) {
        hasActiveChildTranslation = false;
        inProgressLine?.classList.add("hidden");
        const reportUrl = heartbeatData.getAttribute("data-mt-report-url");
        showReportBanners(document.getElementById("mt-source-report-banner"), reportUrl ?? undefined);
    }
};

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
    clearInterval(heartbeatInterval);

    const url = heartbeatData.getAttribute("data-heartbeat-url");
    const payload = heartbeatData.getAttribute("data-heartbeat-payload");
    const languageSlug = heartbeatData.getAttribute("data-language-slug");
    const cancelUrl = heartbeatData.getAttribute("data-cancel-url");
    const result = await sendMessage(url, JSON.stringify({ key: payload, force: false, languageSlug }));
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
                    window.removeEventListener("pagehide", unloadEventListener);
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
        // Independent of the lock check below - a page can simultaneously be
        // a translation target (locked for editing) and a translation source
        // (just triggering translations into its children), so this runs
        // regardless of which of the branches below fires.
        updateChildTranslationProgress(heartbeatData, result.activeChildTranslationTaskId);

        if (result.currentlyInMachineTranslation) {
            if (!isMachineTranslationLockShowing) {
                isMachineTranslationLockShowing = true;
                document.getElementById("popup-overlay")?.classList.remove("hidden");
                document.getElementById("machine-translation-lock-dialog")?.classList.remove("hidden");
            }
            // Poll faster while translation is in progress, to reload soon after it finishes
            const machineTranslationIntervalLength = 5_000;
            heartbeatInterval = setInterval(() => sendHeartbeat(heartbeatData), machineTranslationIntervalLength);
        } else if (isMachineTranslationLockShowing) {
            // Translation finished while we were waiting - reload to pick up the fresh content.
            // window.location.reload() does not correctly work if the view is rendered after a post request, because then
            // the browser tries to re-send the post request
            /* eslint-disable-next-line no-self-assign */
            window.location.href = window.location.href;
            return;
        } else {
            // Sends a heartbeat every 10 seconds
            const intervalLength = 10_000;
            heartbeatInterval = setInterval(() => sendHeartbeat(heartbeatData), intervalLength);
        }
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
    unloadEventListener = () => {
        const data = new FormData();
        data.append("csrfmiddlewaretoken", getCsrfToken());
        data.append("body", heartbeatPayload);
        navigator.sendBeacon(lockReleaseUrl, data);
    };
    window.addEventListener("pagehide", unloadEventListener);
};

window.addEventListener("load", setupHeartbeat);
