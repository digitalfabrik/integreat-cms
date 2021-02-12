u('.collapsible').each(function(node){
    u(node).on('click', toggle_dashboard_section);
});

/**
 * Handles toggling boxes on the dashboard
 * @param {Event} event Click event for dashboard containers
 */
function toggle_dashboard_section(event){
    // The button which was clicked
    let button = u(event.target).closest('.collapsible');
    // The div which should be collapsed or expanded
    let content = button.parent().find('.collapsible-content')
    // Toggle content div
    content.toggleClass('active');
    // Toggle arrows
    if (content.hasClass('active')){
        button.find('.up-arrow').removeClass('hidden');
        button.find('.down-arrow').addClass('hidden');
    } else {
        button.find('.up-arrow').addClass('hidden');
        button.find('.down-arrow').removeClass('hidden');
    }
}
