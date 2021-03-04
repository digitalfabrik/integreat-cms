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
});