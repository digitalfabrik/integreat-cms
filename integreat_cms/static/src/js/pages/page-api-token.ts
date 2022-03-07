/*
 * Generate and (un)set the API token.
 */

import { copyToClipboard } from "../copy-clipboard";

// Set event handler
window.addEventListener("load", () => {
    document.getElementById("id_enable_api_token")?.addEventListener("change", setApiToken);
    document.getElementById("copy-api-token")?.addEventListener("click", copyApiToken)
});


/**
 * Generate a UUID and set as API token
 *
 * @param {target} eventTarget - The enable api token checkbox
 */
function setApiToken({ target }: Event) {
    let checkBox = target as HTMLInputElement;
    let text = document.getElementById("id_api_token") as HTMLInputElement;
    let apiTokenContainer = document.getElementById("api-token-container") as HTMLInputElement;
    if (checkBox.checked){
        text.value = self.crypto.randomUUID();
        apiTokenContainer.classList.remove("hidden");
    } else {
        text.value = "";
        apiTokenContainer.classList.add("hidden");
    }
}

/**
 * Copy API token to clipboard
 *
 * @param event Event - The click event
 */
function copyApiToken(event: Event) {
    event.preventDefault();
    let text = document.getElementById("id_api_token") as HTMLInputElement;
    let copyButton = document.getElementById("copy-api-token");
    let successBox = document.getElementById("copy-api-token-success");
    // Copy value to clipboard
    copyToClipboard(text.value);
    // Indicate success by changing button
    copyButton.classList.add("hidden");
    successBox.classList.remove("hidden");
    // Revert button after 3 seconds
    setTimeout(function() {
        successBox.classList.add("hidden");
        copyButton.classList.remove("hidden");
    }, 3 * 1000);
}
