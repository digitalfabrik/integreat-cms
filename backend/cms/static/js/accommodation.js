// event handler for showing confirmation popups
u('.confirmation-button').each(function(node) {
    u(node).handle('click', show_confirmation_popup);
});
function show_confirmation_popup(e) {
    let button = u(e.target).closest('button');
    let confirmation_popup = u(button.attr('data-confirmation-popup'));
    confirmation_popup.find('.accommodation-title').html(button.attr('data-accommodation-title'));
    confirmation_popup.find('form').attr('action', button.attr('data-action'));
    confirmation_popup.addClass('flex');
    confirmation_popup.removeClass('hidden');
    u('#popup-overlay').removeClass('hidden');
}

// event handler for closing confirmation popups
u('.confirmation-popup').each(function(node) {
    u(node).find('button').handle('click', close_confirmation_popup);
});
function close_confirmation_popup(e) {
    u('#popup-overlay').addClass('hidden');
    let confirmation_popup = u(e.target).closest('.confirmation-popup');
    confirmation_popup.addClass('hidden');
    confirmation_popup.removeClass('flex');
}

u('#id_spoken_languages').attr('style', 'list-style: none');
