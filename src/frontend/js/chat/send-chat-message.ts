import feather from "feather-icons";
import { refreshChatDeleteHandlers } from "./delete-chat-message";
/**
 * This file contains the sending function for the author chat
 */

window.addEventListener("load", () => {
  const chatForm = document.getElementById("chat-form");
  if (chatForm) {
    // Set event listener
    chatForm.addEventListener("submit", sendChatMessage);
  }
});

// Function to be executed when chat form is submitted
async function sendChatMessage(event: Event) {
  event.preventDefault();
  // Disable submit button to prevent accidental multiple submits
  const sendChangeMessage = document.getElementById(
    "send-chat-message"
  ) as HTMLButtonElement;
  const chatNetworkError = document.getElementById("chat-network-error");
  const chatServerError = document.getElementById("chat-server-error");
  const chatLoading = document.getElementById("chat-loading");
  const chatForm = document.getElementById("chat-form") as HTMLFormElement;
  const chatHistory = document.getElementById("chat-history");

  sendChangeMessage.disabled = true;
  // Hide error in case it was shown before
  chatNetworkError.classList.add("hidden");
  chatServerError.classList.add("hidden");

  // Show loading icon
  chatLoading.classList.remove("hidden");

  try {
    // Submit chat message
    const response = await fetch(chatForm.getAttribute("action"), {
      method: "POST",
      body: new FormData(chatForm),
    });

    // HTTP status 201 Created means the chat message was sent successfully
    if (response.status === 201) {
      // The response text contains the rendered message html
      const data = await response.text();

      // Insert new chat message (at the top because due to flex-col-reverse, the entries are reversed)
      const node = document.createElement('div');
      node.innerHTML = data;
      chatHistory.prepend(node.firstElementChild);
      // Clear input field
      chatForm.reset();
      // Trigger icon replacement
      feather.replace();

      refreshChatDeleteHandlers();
    } else {
      // Throw error which will then be caught later
      throw new Error(
        "Chat message could not be sent: HTTP status " +
          response.status +
          " " +
          response.statusText
      );
    }
  } catch (error) {
    console.log(error);
    if (error instanceof TypeError) {
      // Handle network error
      chatNetworkError.classList.remove("hidden");
    } else {
      // Handle server error
      chatServerError.classList.remove("hidden");
    }
  } finally {
    chatLoading.classList.add("hidden");
    sendChangeMessage.disabled = false;
  }
}
