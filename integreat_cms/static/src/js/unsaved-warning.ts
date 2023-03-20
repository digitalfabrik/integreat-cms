/**
 * This file contains a function to warn the user when they leave a content without saving
 */

let contentModelChanged = false;

window.addEventListener("beforeunload", (event) => {
    // trigger only when something is edited and no submit/save button clicked
    if (contentModelChanged) {
        event.preventDefault();
        /* eslint-disable-next-line no-param-reassign */
        event.returnValue = "This content is not saved. Would you leave the page?";
    }
});

window.addEventListener("load", () => {
    const form = document.querySelector("[data-unsaved-warning]");
    const contentEditArea = document.getElementById("content_model_area");
    // checks whether the user typed something in the content
    ["input", "click", "drag"].forEach((event) => {
        contentEditArea?.addEventListener(event, () => {
            if (!contentModelChanged) {
                console.debug("change on content model detected, enabled beforeunload warning");
            }
            contentModelChanged = true;
        });
    });
    // checks whether the user has saved or submitted the content
    form?.addEventListener("submit", () => {
        contentModelChanged = false;
        console.debug("form submitted, disabled beforeunload warning");
    });
    // removes the warning on autosave
    form?.addEventListener("autosave", () => {
        contentModelChanged = false;
        console.debug("Autosave, disabled beforeunload warning");
    });
});
