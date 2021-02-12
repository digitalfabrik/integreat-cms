/*
 * This file contains functions to show and hide conditional fields
 */

// event handler to toggle push notification fields
u("#id_push_notifications_enabled").on('click', function(event) {
    if (event.target.checked) {
        u("#push-notifications-toggle-div").removeClass('hidden');
    } else {
        u("#push-notifications-toggle-div").addClass('hidden');
    }
});
// event handler to toggle statistic fields
u("#id_statistics_enabled").on('click', function(event) {
    if (event.target.checked) {
        u("#statistics-toggle-div").removeClass('hidden');
    } else {
        u("#statistics-toggle-div").addClass('hidden');
    }
});
