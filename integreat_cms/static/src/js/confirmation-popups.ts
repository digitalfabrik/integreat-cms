/**
 * This file contains all functions which are needed for toggling the confirmation popup
 */
import { off, on } from "./utils/wrapped-events";

type EventHandler = (event: Event) => any;
const handlers = new Map<HTMLElement, EventHandler>();

window.addEventListener("load", () => {
  // event handler for showing confirmation popups
  refreshAjaxConfirmationHandlers();
  // event handler for closing confirmation popups
  document.getElementById("close-confirmation-popup")?.addEventListener("click", closeConfirmationPopup);
});


export function refreshAjaxConfirmationHandlers(ajaxHandler?: (e: Event) => Promise<any> | void) {
  if (ajaxHandler) {
    document
      .querySelectorAll(".confirmation-button")
      .forEach((button) =>
          off(button, "action-confirmed")
      );
    document
      .querySelectorAll(".confirmation-button")
      .forEach((button) =>
          on(button,"action-confirmed", ajaxHandler)
      );
  }
  document
    .querySelectorAll(".confirmation-button")
    .forEach((button) =>
        off(button, "click")
    );
  document
    .querySelectorAll(".confirmation-button")
    .forEach((button) =>
        on(button,"click", showConfirmationPopup)
    );
}

export function showConfirmationPopup(event: Event) {
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

  // If ajax mode is enabled, trigger custom event instead of submitting the form
  if (confirmationPopup.getAttribute("data-ajax")) {
    // Handle form submission differently
    const handler = (event: Event) => handleSubmit(event, button);
    handlers.set(confirmationPopup, handler);
    confirmationPopup.querySelector("form").addEventListener("submit", handler);
  }
}

function handleSubmit(event: Event, button: HTMLButtonElement) {
  // Trigger the custom "action-confirmed" event of the source button
  button.dispatchEvent(new Event("action-confirmed"));
  // Close conformation popup
  closeConfirmationPopup(event);
}

function closeConfirmationPopup(event: Event) {
  event.preventDefault();
  // Hide confirmation popup
  document.getElementById("popup-overlay").classList.add("hidden");
  const confirmationPopup = document.getElementById("confirmation-dialog");
  confirmationPopup.classList.add("hidden");

  // If ajax mode is enabled, remove custom event handler which was inserted in the showConfirmationPopup() function
  if (confirmationPopup.getAttribute("data-ajax")) {
    // Handle form submission differently
    if (handlers.has(confirmationPopup)) {
      confirmationPopup
        .querySelector("form")
        .removeEventListener("submit", handlers.get(confirmationPopup));
    }
  }
}
