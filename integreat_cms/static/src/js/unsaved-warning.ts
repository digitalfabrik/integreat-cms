/**
 * This file contains a function to warn the user when they leave a content without saving
 */

let dirty = false;
let conditionalWarning = false;

import { toggleUnsavedWarningTrue, toggleUnsavedWarningFalse } from "./forms/autosave";
import { contentAreaChanged } from "./forms/tinymce-init";

window.addEventListener("beforeunload", (event) => {
    const form = document.getElementById("content_form") as HTMLFormElement;
    // trigger only when something will not be saved
    if ((form && !(new FormData(form)).get("title"))||(!contentAreaChanged && conditionalWarning) ||dirty) {
        toggleUnsavedWarningTrue();
        event.preventDefault();
        /* eslint-disable-next-line no-param-reassign */
        event.returnValue = "This content is not saved. Would you leave the page?";
    }
});

window.addEventListener("load", () => {
    const form = document.querySelector("[data-unsaved-warning]");
    // checks whether the user typed something in the content
    form?.addEventListener("input", (event) => {
        // does not set the dirty flag, if the event target is explicitly excluded
        const target = event.target as HTMLElement;
        if (target.hasAttribute("data-unsaved-warning-exclude")) {
            return;
        }
        if (target.hasAttribute("conditional-warning")) {
            conditionalWarning = true;
            return;
        }
        if (!dirty) {
            console.debug("editing detected, enabled beforeunload warning");
        }
        dirty = true;
    });
    // checks whether the user has saved or submitted the content
    form?.addEventListener("submit", () => {
        dirty = false;
        console.debug("form submitted, disabled beforeunload warning");
    });
    // removes the warning on autosave
    form?.addEventListener("autosave", () => {
        dirty = false;
        conditionalWarning = false;
        toggleUnsavedWarningFalse();
        console.debug("Autosave, disabled beforeunload warning");
    });
});
