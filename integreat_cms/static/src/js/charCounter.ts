/**
 * This file contains a function to count the input length of push notifications
 */

// Function to update the content length of a push notification
function updateLengthCounter(this: HTMLElement, textarea: HTMLFormElement) {
    this.textContent = textarea.value.length;
}

window.addEventListener("load", () => {
    // Get all text areas for push notifications (select textarea nodes where the name attribute begins with "form-" and ends with "-text")
    const counter = document.getElementById("input-length-counter");

    if (counter) {
        const textarea = document.getElementById("id_text");
        updateLengthCounter.bind(counter)(textarea as HTMLFormElement);
        ["onkeyup", "input"].forEach((event: string) => {
            textarea.addEventListener(event, updateLengthCounter.bind(counter, textarea as HTMLFormElement));
        });
    }
});
