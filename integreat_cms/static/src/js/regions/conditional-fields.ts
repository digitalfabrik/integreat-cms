/*
 * This file contains functions to show and hide conditional fields
 */

const updateTimezoneAreaDropdown = (event?: Event) => {
    const timezoneAreaDropdown = document.getElementById("id_timezone_area") as HTMLSelectElement;
    const timezoneDropdown = document.getElementById("id_timezone") as HTMLSelectElement;
    // Reset timezone value when timezone region is changed
    if (event !== undefined) {
        timezoneDropdown.value = "";
    }
    // Hide all sub-timzones of other areas
    timezoneDropdown
        .querySelectorAll(`option:not([value*="${timezoneAreaDropdown.value}"],[value=""])`)
        .forEach((option) => option.classList.add("hidden"));
    // Show all sub-timezones of the selected area
    timezoneDropdown
        .querySelectorAll(`option[value*="${timezoneAreaDropdown.value}"]`)
        .forEach((option) => option.classList.remove("hidden"));
};

// event handler to toggle push notification fields
window.addEventListener("load", () => {
    const enablePushNotificationButton = document.getElementById("id_push_notifications_enabled");
    const pushNotificationsToggle = document.getElementById("push-notifications-toggle-div");
    if (enablePushNotificationButton && pushNotificationsToggle) {
        enablePushNotificationButton.addEventListener("click", ({ target }) => {
            if ((target as HTMLInputElement).checked) {
                pushNotificationsToggle.classList.remove("hidden");
            } else {
                pushNotificationsToggle.classList.add("hidden");
            }
        });
    }

    // event handler for auto-filling DeepL renewal budget year start month
    const midyearDateEnabledCheckbox = document.getElementById("id_deepl_midyear_start_enabled");
    const midyearDateSelector = document.getElementById("id_deepl_midyear_start_month") as HTMLSelectElement;
    if (midyearDateEnabledCheckbox && midyearDateSelector) {
        midyearDateEnabledCheckbox.addEventListener("click", ({ target }) => {
            if ((target as HTMLInputElement).checked && !midyearDateSelector.value) {
                const currentDate = new Date();
                midyearDateSelector.value = String(currentDate.getMonth());
            }
        });
    }

    // add conditional logic to display options within the second timezone dropdown
    const timezoneAreaDropdown = document.getElementById("id_timezone_area") as HTMLSelectElement;
    const timezoneDropdown = document.getElementById("id_timezone") as HTMLSelectElement;

    if (timezoneDropdown && timezoneAreaDropdown) {
        updateTimezoneAreaDropdown();
        timezoneAreaDropdown.addEventListener("change", updateTimezoneAreaDropdown);
    }
});
