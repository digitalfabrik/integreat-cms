/**
 * This file contains a function to count the input length of push notifications
 */

window.addEventListener("load", () => {
    // Get all text areas for push notifications (select textarea nodes where the name attribute begins with "form-" and ends with "-text")
    document.querySelectorAll("textarea[name^=form-][name$=-text]").forEach((textarea: Element) => {
        // Get input length counter which belongs to this textarea
        let counter = textarea.parentElement.getElementsByClassName("input-length-counter")[0] as HTMLElement;
        // Update the input length counter once initially
        updateLengthCounter.bind(counter)(textarea as HTMLFormElement);
        // Use both "onkeyup" and "input" events to handle keyboard inputs and copy/paste via the clipboard
        ["onkeyup", "input"].forEach((event: string) => {
            // set event handler for updating the length of push notifications
            textarea.addEventListener(event, updateLengthCounter.bind(counter, textarea as HTMLFormElement));
        });
    });
});

// Function to update the content length of a push notification
function updateLengthCounter(this: HTMLElement, textarea: HTMLFormElement) {
    this.textContent = textarea.value.length;
}
