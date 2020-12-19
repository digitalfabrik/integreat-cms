u('.collapsible').each(function(node){
    u(node).on('click', toggle_dashboard_section);
});

/**
 * Handles toggling the RSS feed
 * @param {Event} e Click event for RSS feed
 */
function toggle_dashboard_section(e){
    u('.collapsible-content').toggleClass('active');
    if (u('.collapsible-content').hasClass('active')){
        u('#up-arrow').removeClass('hidden');
        u('#down-arrow').addClass('hidden');
    } else {
        u('#up-arrow').addClass('hidden');
        u('#down-arrow').removeClass('hidden');
    }
}
