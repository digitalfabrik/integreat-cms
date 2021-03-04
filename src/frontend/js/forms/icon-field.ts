/*
 * This file contains all functions used for the icon field
 */

// Set event handlers
u('#id_icon').on('change', updateIconDisplay);
u('#remove-icon').on('click', removeIcon);
u('#restore-icon').on('click', setIcon);

/**
 * Listen for user input (selection in file browser) for uploading icons.
 * Updates the icon preview and UI for clearing.
 *
 * @param {Event} event - selected icon changed
 */
function updateIconDisplay(event) {
    const files = u(event.target).first().files;
    // Fill in uploaded file path
    u('#icon_preview').find("img").attr("src", URL.createObjectURL(files[0]))
    u('#icon_filename').text(files[0].name);
    // Update UI elements
    setIcon();
}

/**
 * Handles all UI elements when an icon is removed
 */
function removeIcon() {
    // Hide preview
    u('#icon_preview').addClass("hidden");
    // Change icon label
    u('#change-icon-label').addClass("hidden");
    u('#set-icon-label').removeClass("hidden");
    // Toggle remove/restore buttons
    u('#remove-icon').addClass("hidden");
    u('#restore-icon').removeClass("hidden");
    // Set clear-checkbox
    u('#icon-clear_id').first().checked = true;
}

/**
 * Handles all UI elements when an icon is selected or restored
 */
function setIcon() {
    // Show preview
    u('#icon_preview').removeClass("hidden");
    // Change icon label
    u('#set-icon-label').addClass("hidden");
    u('#change-icon-label').removeClass("hidden");
    // Toggle remove/restore buttons
    u('#restore-icon').addClass("hidden");
    u('#remove-icon').removeClass("hidden");
    // Unset clear-checkbox
    u('#icon-clear_id').first().checked = false;
}
