/**
 * This file contains all functions which are needed for toggling the confirmation popup
 */
import { off, on } from "./utils/wrapped-events";

type EventHandler = (event: Event) => any;

let submit_handler: EventHandler | null = null;
let cancel_handler: EventHandler | null = null;

window.addEventListener("load", () => {
    // On the page tree, the event listeners are set after all subpages have been loaded
    if (!document.querySelector("[data-delay-event-handlers]")) {
        addConfirmationDialogListeners();
    }
});

export function addConfirmationDialogListeners() {
    // event handler for showing confirmation popups
    document.querySelectorAll(".confirmation-button").forEach((button) => on(button, "click", showConfirmationPopup));
}

// Configures all objects that match `selector` to show a confirmation dialog on click.
// On confirm `handler` gets invoked.
export function refreshAjaxConfirmationHandlers(selector: string, handler: (e: Event) => Promise<any> | void) {
    const elements = document.querySelectorAll(selector);

    elements.forEach((button) => {
        off(button, "click");
        on(button, "click", showConfirmationPopupAjax);

        off(button, "action-confirmed");
        on(button, "action-confirmed", handler);
    });
}

export function showConfirmationPopupWithData(
    subject: string,
    title: string,
    text: string,
    on_submit?: (event: Event) => void,
    on_cancel?: (event: Event) => void
): HTMLElement {
    // Set confirmation data
    document.getElementById("confirmation-subject").textContent = subject;
    document.getElementById("confirmation-title").textContent = title;
    document.getElementById("confirmation-text").textContent = text;
    const confirmationPopup = document.getElementById("confirmation-dialog");

    // Set submit and cancel handlers
    submit_handler = (event: Event) => {
        try {
            if (on_submit !== undefined) {
                event.preventDefault();
                on_submit(event);
            }
        } finally {
            closeConfirmationPopup();
        }
    };
    confirmationPopup.querySelector("form").addEventListener("submit", submit_handler);
    cancel_handler = (event: Event) => {
        try {
            if (on_cancel !== undefined) on_cancel(event);
        } finally {
            closeConfirmationPopup();
            event.preventDefault();
        }
    };
    document.getElementById("close-confirmation-popup")?.addEventListener("click", cancel_handler);

    // Show confirmation popup
    confirmationPopup.classList.remove("hidden");
    document.getElementById("popup-overlay").classList.remove("hidden");

    return confirmationPopup;
}

export function showConfirmationPopup(event: Event, submit_handler?: (event: Event) => void): HTMLElement {
    event.preventDefault();
    const button = (event.target as HTMLElement).closest("button");
    const confirmationPopup = showConfirmationPopupWithData(
        button.getAttribute("data-confirmation-subject"),
        button.getAttribute("data-confirmation-title"),
        button.getAttribute("data-confirmation-text"),
        submit_handler
    );
    confirmationPopup.querySelector("form").setAttribute("action", button.getAttribute("data-action"));

    return confirmationPopup;
}

// If ajax mode is enabled, trigger custom event instead of submitting the form
export function showConfirmationPopupAjax(event: Event) {
    const button = (event.target as HTMLElement).closest("button");
    const handler = (_: Event) => button.dispatchEvent(new Event("action-confirmed"));

    showConfirmationPopup(event, handler);
}

function closeConfirmationPopup() {
    // Hide confirmation popup
    document.getElementById("popup-overlay").classList.add("hidden");
    const confirmationPopup = document.getElementById("confirmation-dialog");
    confirmationPopup.classList.add("hidden");

    if (submit_handler !== null) {
        confirmationPopup.querySelector("form").removeEventListener("submit", submit_handler);
        submit_handler = null;
    }

    if (cancel_handler !== null) {
        document.getElementById("close-confirmation-popup")?.removeEventListener("click", cancel_handler);
        cancel_handler = null;
    }
}
