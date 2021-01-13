function reset_filter(event) {
    u(event.target).closest('form').find('input').each((node) => {
        if (u(node).is('[type=checkbox]')) {
            if (u(node).hasClass('default-checked')) {
                // Checkbox marked to be checked by default
                u(node).first().checked = true;
            } else if (u(node).hasClass('default-not-checked')) {
                // Checkbox marked to be unchecked by default
                u(node).first().checked = false;
            }
        } else if (u(node).hasClass('default-value')) {
            // Non-checkbox input marked to have a default value
            u(node).first().value = u(node).data('default-value');
        }
    });
}