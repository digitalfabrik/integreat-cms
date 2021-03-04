/**
 * This file contains the sending function for the author chat
 */

// Set event listener
u('#chat-form').handle('submit', send_chat_message);

// Function to be executed when chat form is submitted
async function send_chat_message() {
    // Disable submit button to prevent accidental multiple submits
    u("#send-chat-message").first().disabled = true;
    // Hide error in case it was shown before
    u('#chat-network-error').addClass("hidden");
    u('#chat-server-error').addClass("hidden");
    // Show loading icon
    u('#chat-loading').removeClass("hidden");

    // Submit chat message
    fetch(u(this).attr('action'), {
        method: 'POST',
        body: new FormData(this)
    }).then(function (response) {
        // HTTP status 201 Created means the chat message was sent successfully (status 200 OK could also mean CSRF error)
        if (response.status === 201) {
            // The response text contains the rendered message html
            return response.text();
        } else {
            // Throw error which will then be caught later
            throw new Error("Chat message could not be sent: HTTP status " + response.status + " " + response.statusText);
        }
    }).then(data => {
        // Insert new chat message (at the top because due to flex-col-reverse, the entries are reversed)
        u('#chat-history').prepend(data);
        // Clear input field
        u('#chat-form').first().reset();
        // Trigger icon replacement
        feather.replace();
        // Reset event listeners for delete buttons
        u('.confirmation-button').off('action-confirmed');
        u('.confirmation-button').handle('action-confirmed', delete_chat_message);
        u('.confirmation-button').off('click');
        u('.confirmation-button').handle('click', show_confirmation_popup);
    }).catch(error => {
        console.log(error);
        if (error instanceof TypeError) {
            // Handle network error
            u('#chat-network-error').removeClass("hidden");
        } else {
            // Handle server error
            u('#chat-server-error').removeClass("hidden");
        }
    }).finally(() => {
        // Hide loading icon
        u('#chat-loading').addClass("hidden");
        // Enable form submitting again
        u("#send-chat-message").first().disabled = false;
    });
}
