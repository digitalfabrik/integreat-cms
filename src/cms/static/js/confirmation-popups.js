/**
 * This file contains all functions which are needed for toggling the confirmation popup
 */

// event handler for showing confirmation popups
u('.confirmation-button').handle('click', show_confirmation_popup);
// event handler for closing confirmation popups
u('#confirmation-dialog').find('button').handle('click', close_confirmation_popup);

function show_confirmation_popup(event) {
    let button = u(event.target).closest('button');
    // Set confirmation data
    u('#confirmation-subject').html(button.data('confirmation-subject'));
    u('#confirmation-title').html(button.data('confirmation-title'));
    u('#confirmation-text').html(button.data('confirmation-text'));
    let confirmation_popup = u('#confirmation-dialog');
    confirmation_popup.find('form').attr('action', button.data('action'));
    // Show confirmation popup
    confirmation_popup.removeClass('hidden');
    u('#popup-overlay').removeClass('hidden');

    // If ajax mode is enabled, trigger custom event instead of submitting the form
    if (confirmation_popup.data("ajax")) {
        // Handle form submission differently
        confirmation_popup.find("form").handle("submit", function() {
            // Trigger the custom "action-confirmed" event of the source button
            button.trigger("action-confirmed");
            // Close conformation popup
            close_confirmation_popup();
        });
    }
}

function close_confirmation_popup() {
    // Hide confirmation popup
    u('#popup-overlay').addClass('hidden');
    let confirmation_popup = u('#confirmation-dialog');
    confirmation_popup.addClass('hidden');

    // If ajax mode is enabled, remove custom event handler which was inserted in the show_confirmation_popup() function
    if (confirmation_popup.data("ajax")) {
        // Handle form submission differently
        confirmation_popup.find("form").off("submit");
    }
}
