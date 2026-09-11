import { off, on } from "./wrapped-events";

type EventHandler = (event: Event) => any;

let submitHandler: EventHandler | null = null;
let cancelHandler: EventHandler | null = null;

const closeConfirmationPopup = () => {
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
    document.getElementById("confirmation-subject").textContent = subject;
    document.getElementById("confirmation-title").textContent = title;
    document.getElementById("confirmation-text").textContent = text;
    const confirmationPopup = document.getElementById("confirmation-dialog");

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

    confirmationPopup.classList.remove("hidden");
    document.getElementById("popup-overlay").classList.remove("hidden");

    return confirmationPopup;
};

export const showConfirmationPopup = (event: Event, onSubmit?: (event: Event) => void): HTMLElement => {
    event.preventDefault();
    const button = (event.target as HTMLElement).closest("button");
    const confirmationPopup = showConfirmationPopupWithData(
        button.getAttribute("data-confirmation-subject"),
        button.getAttribute("data-confirmation-title"),
        button.getAttribute("data-confirmation-text"),
        onSubmit
    );
    const referencedPlaceTitle = button.getAttribute("data-confirmation-referenced-place-title");
    document.getElementById("confirmation-referenced-place-title").textContent = referencedPlaceTitle ?? "";
    const referencedPlaceSubject = button.getAttribute("data-confirmation-referenced-place-subject");
    document.getElementById("confirmation-referenced-place-subject").textContent = referencedPlaceSubject ?? "";
    const action = button.getAttribute("data-action");
    if (action) {
        const url = new URL(action, window.location.origin);
        if (url.origin === window.location.origin) {
            confirmationPopup.querySelector("form").action = url.pathname + url.search;
        }
    }

    return confirmationPopup;
};

export const showConfirmationPopupAjax = (event: Event) => {
    const button = (event.target as HTMLElement).closest("button");
    const handler = (_: Event) => button.dispatchEvent(new Event("action-confirmed"));
    showConfirmationPopup(event, handler);
};

export const addConfirmationDialogListeners = () => {
    document.querySelectorAll(".confirmation-button").forEach((button) => on(button, "click", showConfirmationPopup));
};

export const refreshAjaxConfirmationHandlers = (selector: string, handler: (e: Event) => Promise<any> | void) => {
    const elements = document.querySelectorAll(selector);
    elements.forEach((button) => {
        off(button, "click");
        on(button, "click", showConfirmationPopupAjax);
        off(button, "action-confirmed");
        on(button, "action-confirmed", handler);
    });
};
