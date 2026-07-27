import { addConfirmationDialogListeners } from "./utils/confirmation-popup";

window.addEventListener("load", () => {
    // On the page tree, the event listeners are set after all subpages have been loaded
    if (!document.querySelector("[data-delay-event-handlers]")) {
        addConfirmationDialogListeners();
    }
});
