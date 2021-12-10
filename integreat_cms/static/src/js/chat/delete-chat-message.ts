/**
 * This file contains the deletion function for the author chat
 */
import { getCsrfToken } from "../utils/csrf-token";
import { refreshAjaxConfirmationHandlers } from "../confirmation-popups";

// Listen on the custom event "action-confirmed" which is triggered by the confirmation popup
window.addEventListener("load", () => refreshAjaxConfirmationHandlers(".button-delete-chat-message", deleteChatMessage));

// Function to delete a chat message
export async function deleteChatMessage(event: Event) {
  event.preventDefault();
  const chatNetworkError = document.getElementById("chat-network-error");
  const chatServerError = document.getElementById("chat-server-error");

  // Hide error in case it was shown before
  chatNetworkError.classList.add("hidden");
  chatServerError.classList.add("hidden");

  // Delete chat message
  const deletionButton = (event.target as HTMLElement).closest(
    ".button-delete-chat-message"
  );
  try {
    const response = await fetch(deletionButton.getAttribute("data-action"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      }
    });
    if (response.status === 200) {
      // If message was deleted successfully, remove the div containing the message
      deletionButton.closest(".chat-message").remove();
    } else {
      // Throw error which will then be caught later
      throw new Error(
        "Chat message could not be deleted: HTTP status " +
          response.status +
          " " +
          response.statusText
      );
    }
  } catch (error) {
    console.error("Deleting Chat Message failed:", error);
    if (error instanceof TypeError) {
      // Handle network error
      chatNetworkError.classList.remove("hidden");
    } else {
      // Handle server error
      chatServerError.classList.remove("hidden");
    }
  }
}
