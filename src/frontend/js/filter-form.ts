/*
 * Scripts for filter forms
 */

// event handler to toggle filter form
u('#filter-toggle').on('click', () => {
    u('#filter-form-container').toggleClass('hidden');
    u('.filter-toggle-text').toggleClass('hidden');
});

// event handler to reset filter form
u('#filter-reset').on('click', reset_filter);
function reset_filter(event) {
    u(event.target).closest('form').find('input').each(reset_to_default_value);
    u(event.target).closest('form').find('select').each(reset_to_default_value);
}

function reset_to_default_value(node) {
    if (u(node).is('[type=checkbox]')) {
        if (u(node).hasClass('default-checked')) {
            // Checkbox marked to be checked by default
            node.checked = true;
        } else if (u(node).hasClass('default-not-checked')) {
            // Checkbox marked to be unchecked by default
            node.checked = false;
        }
    } else if (u(node).hasClass('default-value')) {
        // Non-checkbox input marked to have a default value
        node.value = u(node).data('default-value');
    }
}
