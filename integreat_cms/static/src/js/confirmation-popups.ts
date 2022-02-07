/**
 * This file contains all functions which are needed for toggling the confirmation popup
 */
import { off, on } from "./utils/wrapped-events";

type EventHandler = (event: Event) => any;
const handlers = new Map<HTMLElement, EventHandler>();

window.addEventListener("load", () => {
  addConfirmationDialogListeners();
});

export function addConfirmationDialogListeners () {
  // event handler for showing confirmation popups
  document
    .querySelectorAll(".confirmation-button")
    .forEach((button) =>
      on(button, "click", showConfirmationPopup)
    );
  document.getElementById("close-confirmation-popup")?.addEventListener("click", closeConfirmationPopup);
}

// Configures all objects that match `selector` to show a confirmation dialog on click.
// On confirm `handler` gets invoked.
export function refreshAjaxConfirmationHandlers(selector: string, handler: (e: Event) => Promise<any> | void) {
  const elements = document.querySelectorAll(selector);

  elements.forEach((button) => {
    off(button, "click");
    on(button, "click", showConfirmationPopupAjax);

    off(button, "action-confirmed");
    on(button, "action-confirmed", handler)
  });

}

export function showConfirmationPopup(event: Event): HTMLElement {
  event.preventDefault();
  const button = (event.target as HTMLElement).closest("button");
  // Set confirmation data
  document.getElementById(
    "confirmation-subject"
  ).textContent = button.getAttribute("data-confirmation-subject");
  document.getElementById("confirmation-title").textContent = button.getAttribute(
    "data-confirmation-title"
  );
  document.getElementById("confirmation-text").textContent = button.getAttribute(
    "data-confirmation-text"
  );
  const confirmationPopup = document.getElementById("confirmation-dialog");
  confirmationPopup
    .querySelector("form")
    .setAttribute("action", button.getAttribute("data-action"));
  // Show confirmation popup
  confirmationPopup.classList.remove("hidden");
  document.getElementById("popup-overlay").classList.remove("hidden");

  return confirmationPopup;
}

// If ajax mode is enabled, trigger custom event instead of submitting the form
export function showConfirmationPopupAjax(event: Event) {
  const confirmationPopup = showConfirmationPopup(event);

  const button = (event.target as HTMLElement).closest("button");
  const handler = (event: Event) => handleSubmit(event, button);
  handlers.set(confirmationPopup, handler);
  confirmationPopup.querySelector("form").addEventListener("submit", handler);
}

function handleSubmit(event: Event, button: HTMLButtonElement) {
  // Trigger the custom "action-confirmed" event of the source button
  button.dispatchEvent(new Event("action-confirmed"));
  // Close conformation popup
  closeConfirmationPopupAjax(event);
}

function closeConfirmationPopup(event: Event) {
  event.preventDefault();
  // Hide confirmation popup
  document.getElementById("popup-overlay").classList.add("hidden");
  const confirmationPopup = document.getElementById("confirmation-dialog");
  confirmationPopup.classList.add("hidden");
}

function closeConfirmationPopupAjax(event: Event) {
  closeConfirmationPopup(event);
  // If ajax mode is enabled, remove custom event handler which was inserted in the showConfirmationPopup() function
  // Handle form submission differently
  const confirmationPopup = document.getElementById("confirmation-dialog");
  if (handlers.has(confirmationPopup)) {
    confirmationPopup
      .querySelector("form")
      .removeEventListener("submit", handlers.get(confirmationPopup));
  }
}
