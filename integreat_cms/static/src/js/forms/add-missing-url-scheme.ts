/**
 * This file prepends "https://" to the value of URL input fields if the user did not enter a scheme.
 * Otherwise, the browser's built-in validation rejects values like "www.example.com" with an unhelpful error.
 */

import { addMissingUrlScheme } from "../utils/url";

const completeUrl = (target: EventTarget | null) => {
    if (target instanceof HTMLInputElement && target.type === "url" && !target.readOnly && !target.disabled) {
        const completedUrl = addMissingUrlScheme(target.value);
        if (completedUrl !== target.value) {
            target.value = completedUrl;
        }
    }
};

// Use event delegation, so that dynamically added input fields are covered as well.
// The "change" event is fired when the field loses focus after the value was modified.
document.addEventListener("change", (event) => completeUrl(event.target), true);
// When the form is submitted by pressing enter, the browser validates the field before it loses focus
document.addEventListener(
    "keydown",
    (event) => {
        if (event.key === "Enter") {
            completeUrl(event.target);
        }
    },
    true
);
