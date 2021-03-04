/*
 * This file contains functions to show and hide conditional fields
 */

// event handler to show time fields
u("#id_is_all_day").on('click', function(event) {
    if (event.target.checked) {
        u(".time-field").each(function(node) {
            // get plain javascript object of time input field
            let timeInputField = u(node).find('input').first()
            // only change behaviour when value is empty
            if (!timeInputField.getAttribute('value')) {
                // remove empty value attribute because it is no valid time value'
                timeInputField.removeAttribute('value');
                // remove required attribute
                timeInputField.removeAttribute('required');
            }
            // hide input field
            u(node).addClass('hidden');
        });
    } else {
        u(".time-field").each(function(node) {
            // show input field
            u(node).removeClass('hidden');
            // clear value
            u(node).find('input').attr('value', '');
            // make field required
            u(node).find('input').attr('required', true);
        });
    }
});
// event handler to show recurrence rule form
u("#recurrence-rule-checkbox").on('click', function(event){
    if (event.target.checked) {
        u("#recurrence-rule").removeClass('hidden');
    } else {
        u("#recurrence-rule").addClass('hidden');
    }
});
// event handler to show fields for recurrence frequency
u("#id_frequency").on('click', function(event){
    if (event.target.value == 'WEEKLY') {
        u("#recurrence-weekly").removeClass('hidden');
        u("#recurrence-monthly").addClass('hidden');
    } else if (event.target.value == 'MONTHLY') {
        u("#recurrence-monthly").removeClass('hidden');
        u("#recurrence-weekly").addClass('hidden');
    } else {
        u("#recurrence-weekly").addClass('hidden');
        u("#recurrence-monthly").addClass('hidden');
    }
});
// event handler to show recurrence end date
u("#id_has_recurrence_end_date").on('click', function(event){
    if (event.target.checked) {
        u("#recurrence-end").removeClass('hidden');
    } else {
        u("#recurrence-end").addClass('hidden');
    }
});
