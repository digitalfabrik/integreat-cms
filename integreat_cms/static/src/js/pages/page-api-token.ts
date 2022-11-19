/*
 * Generate and (un)set the API token.
 */

import { copyToClipboard } from "../copy-clipboard";

/**
 * Generate a UUID and set as API token
 *
 * @param {target} eventTarget - The enable api token checkbox
 */
const setApiToken = ({ target }: Event) => {
    const checkBox = target as HTMLInputElement;
    const text = document.getElementById("id_api_token") as HTMLInputElement;
    const apiTokenContainer = document.getElementById("api-token-container") as HTMLInputElement;
    if (checkBox.checked) {
        /* eslint-disable-next-line no-restricted-globals */
        text.value = self.crypto.randomUUID();
        apiTokenContainer.classList.remove("hidden");
    } else {
        text.value = "";
        apiTokenContainer.classList.add("hidden");
    }
};

/**
 * Copy API token to clipboard
 *
 * @param event Event - The click event
 */
const copyApiToken = (event: Event) => {
    event.preventDefault();
    const text = document.getElementById("id_api_token") as HTMLInputElement;
    const copyButton = document.getElementById("copy-api-token");
    const successBox = document.getElementById("copy-api-token-success");
    // Copy value to clipboard
    copyToClipboard(text.value);
    // Indicate success by changing button
    copyButton.classList.add("hidden");
    successBox.classList.remove("hidden");
    // Revert button after 3 seconds
    const timeoutDuration = 3000;
    setTimeout(() => {
        successBox.classList.add("hidden");
        copyButton.classList.remove("hidden");
    }, timeoutDuration);
};

// Set event handler
window.addEventListener("load", () => {
    document.getElementById("id_enable_api_token")?.addEventListener("change", setApiToken);
    document.getElementById("copy-api-token")?.addEventListener("click", copyApiToken);
});
