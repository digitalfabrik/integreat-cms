/*
 * This file contains functions to show and hide conditional fields
 */

// event handler to toggle push notification fields
window.addEventListener('load', () => {
    const enablePushNotificationButton = document.getElementById("id_push_notifications_enabled");
    const pushNotificationsToggle = document.getElementById("push-notifications-toggle-div");
    if(enablePushNotificationButton && pushNotificationsToggle) {  
        enablePushNotificationButton.addEventListener('click', ({target}) => {
            if ((target as HTMLInputElement).checked) {
                pushNotificationsToggle.classList.remove('hidden');
            } else {
                pushNotificationsToggle.classList.add('hidden');
            }
        })
    }

    // event handler to toggle statistic fields
    const statisticsEnabled = document.getElementById("id_statistics_enabled");
    const statisticsToggle = document.getElementById("statistics-toggle-div");
    if(statisticsEnabled && statisticsToggle) {
        statisticsEnabled.addEventListener('click', ({target}) => {
            if ((target as HTMLInputElement).checked) {
                statisticsToggle.classList.remove('hidden');
            } else {
                statisticsToggle.classList.add('hidden');
            }
        });
    }
    // add conditional logic to display options within the second timezone dropdown
    const timezoneAreaDropdown = document.getElementById("id_timezone_area") as HTMLSelectElement;
    const timezoneDropdown = document.getElementById("id_timezone") as HTMLSelectElement;
        
    if(timezoneDropdown && timezoneAreaDropdown) {
        updateTimezoneAreaDropdown();
        timezoneAreaDropdown.addEventListener('change', updateTimezoneAreaDropdown)
    }
});

function updateTimezoneAreaDropdown() {
    const timezoneAreaDropdown = document.getElementById("id_timezone_area") as HTMLSelectElement;
    const timezoneDropdown = document.getElementById("id_timezone") as HTMLSelectElement;
    let otherOptions;
    let selectedOptions;
    timezoneDropdown.value = '';
    if (timezoneAreaDropdown.value === '') {
        selectedOptions = [];
        otherOptions = timezoneDropdown.querySelectorAll('option');
    } else {
        otherOptions = timezoneDropdown.querySelectorAll('option:not([value*="' + timezoneAreaDropdown.value + '"])');
        selectedOptions = timezoneDropdown.querySelectorAll('option[value*="' + timezoneAreaDropdown.value + '"]');
    }
    otherOptions.forEach((option) => option.classList.add('hidden'));
    selectedOptions.forEach((option) => option.classList.remove('hidden'));

    timezoneDropdown.querySelector('option[value=""]').classList.remove('hidden');
}