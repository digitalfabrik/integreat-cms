/**
 * This file contains all functions which are needed for toggling the confirmation popup
 */
import { off, on } from "./utils/wrapped-events";

type EventHandler = (event: Event) => any;

let submitHandler: EventHandler | null = null;
let cancelHandler: EventHandler | null = null;

export const showConfirmationPopup = (event: Event, submitHandler?: (event: Event) => void): HTMLElement => {
    event.preventDefault();
    const button = (event.target as HTMLElement).closest("button");
    /* eslint-disable-next-line @typescript-eslint/no-use-before-define */
    const confirmationPopup = showConfirmationPopupWithData(
        button.getAttribute("data-confirmation-subject"),
        button.getAttribute("data-confirmation-title"),
        button.getAttribute("data-confirmation-text"),
        submitHandler
    );
    confirmationPopup.querySelector("form").setAttribute("action", button.getAttribute("data-action"));

    return confirmationPopup;
};

// If ajax mode is enabled, trigger custom event instead of submitting the form
export const showConfirmationPopupAjax = (event: Event) => {
    const button = (event.target as HTMLElement).closest("button");
    const handler = (_: Event) => button.dispatchEvent(new Event("action-confirmed"));

    showConfirmationPopup(event, handler);
};

export const addConfirmationDialogListeners = () => {
    // event handler for showing confirmation popups
    document.querySelectorAll(".confirmation-button").forEach((button) => on(button, "click", showConfirmationPopup));
};

// Configures all objects that match `selector` to show a confirmation dialog on click.
// On confirm `handler` gets invoked.
export const refreshAjaxConfirmationHandlers = (selector: string, handler: (e: Event) => Promise<any> | void) => {
    const elements = document.querySelectorAll(selector);

    elements.forEach((button) => {
        off(button, "click");
        on(button, "click", showConfirmationPopupAjax);

        off(button, "action-confirmed");
        on(button, "action-confirmed", handler);
    });
};

const closeConfirmationPopup = () => {
    // Hide confirmation popup
    document.getElementById("popup-overlay").classList.add("hidden");
    const confirmationPopup = document.getElementById("confirmation-dialog");
    confirmationPopup.classList.add("hidden");

    if (submitHandler !== null) {
        confirmationPopup.querySelector("form").removeEventListener("submit", submitHandler);
        submitHandler = null;
    }

    if (cancelHandler !== null) {
        document.getElementById("close-confirmation-popup")?.removeEventListener("click", cancelHandler);
        cancelHandler = null;
    }
};

export const showConfirmationPopupWithData = (
    subject: string,
    title: string,
    text: string,
    onSubmit?: (event: Event) => void,
    onCancel?: (event: Event) => void
): HTMLElement => {
    // Set confirmation data
    document.getElementById("confirmation-subject").textContent = subject;
    document.getElementById("confirmation-title").textContent = title;
    document.getElementById("confirmation-text").textContent = text;
    const confirmationPopup = document.getElementById("confirmation-dialog");

    // Set submit and cancel handlers
    submitHandler = (event: Event) => {
        try {
            if (onSubmit !== undefined) {
                event.preventDefault();
                onSubmit(event);
            }
        } finally {
            closeConfirmationPopup();
        }
    };
    confirmationPopup.querySelector("form").addEventListener("submit", submitHandler);
    cancelHandler = (event: Event) => {
        try {
            if (onCancel !== undefined) {
                onCancel(event);
            }
        } finally {
            closeConfirmationPopup();
            event.preventDefault();
        }
    };
    document.getElementById("close-confirmation-popup")?.addEventListener("click", cancelHandler);

    // Show confirmation popup
    confirmationPopup.classList.remove("hidden");
    document.getElementById("popup-overlay").classList.remove("hidden");

    return confirmationPopup;
};

window.addEventListener("load", () => {
    // On the page tree, the event listeners are set after all subpages have been loaded
    if (!document.querySelector("[data-delay-event-handlers]")) {
        addConfirmationDialogListeners();
    }
});
