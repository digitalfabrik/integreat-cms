/**
 * This file contains all functions which are needed for the page side by side view dropdown and button.
 */

function toggle_sbs_button(event) {
    if (event.target.value !== '') {
        u('#side-by-side-link').attr('href', event.target.value);
        u('#side-by-side-link').removeClass('bg-gray-400');
        u('#side-by-side-link').removeClass('pointer-events-none');
        u('#side-by-side-link').addClass('bg-blue-500');
        u('#side-by-side-link').addClass('hover:bg-blue-600');
    } else {
        u('#side-by-side-link').first().removeAttribute('href');
        u('#side-by-side-link').removeClass('bg-blue-500');
        u('#side-by-side-link').removeClass('hover:bg-blue-600');
        u('#side-by-side-link').addClass('bg-gray-400');
        u('#side-by-side-link').addClass('pointer-events-none');
    }
}
u(document).handle('DOMContentLoaded', function() {
    u('#side-by-side-select').handle('change', toggle_sbs_button);
    u('#side-by-side-select').trigger('change')
});
