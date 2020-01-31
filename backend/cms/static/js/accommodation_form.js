/*
 * ADD AND REMOVE BED TARGET GROUP FORMS
 *
 * The following event handlers are built to add and remove bed target group forms dynamically.
 * Every time, the add-button is clicked, the last form row gets copied and modified in the following way:
 *     - the ids are counted up by one
 *     - the values are reset
 *     - the total number of forms are incremented
 * Once the maximum number of forms is reached (which is the total number of bed target groups available), it is not possible to add more forms.
 *
 */

u('#add-form-row').handle('click', addBedFormRow);
function addBedFormRow() {
    // get max total number of forms
    let maxNumForms = parseInt(u('#id_beds-MAX_NUM_FORMS').attr('value'));
    // get previous total number of forms
    let total = parseInt(u('#id_beds-TOTAL_FORMS').attr('value'));
    // throw error if cloned form would violate max form rule
    if (total + 1 > maxNumForms) {
        u('#add-form-row').addClass('hidden');
        u('#add-form-row-notice').removeClass('hidden');
        throw "maximum number of forms reached.";
    }

    // clone last form row
    let newElement = u(u('.form-row').last()).clone();

    // set new id of number inputs
    newElement.find('input, select').each((element) => {
        let newName = u(element).attr('name').replace('-' + (total - 1) + '-', '-' + total + '-');
        u(element).attr('name', newName);
        u(element).attr('id', 'id_' + newName);
        u(element).data('previous', '');
        if (newName.includes('target_group') && element.value) {
            // make selected target group option of cloned element disabled
            u(element).find('option[value="' + element.value + '"]').first().disabled = true;
        }
        if (!newName.includes('accommodation')) {
            // discard all values except accommodation
            element.value = '';
        }
        if (newName.includes('DELETE') && element.checked) {
            // if cloned row was a deleted one, uncheck the DELETE checkbox
            element.checked = false;
        }
    });

    // in case the last row was a deleted one, remove the hidden class
    newElement.removeClass('hidden');

    // append to rows
    u('.form-rows').append(newElement);

    // update total number of forms
    u('#id_beds-TOTAL_FORMS').attr('value', total + 1);
}

u('.remove-form-row').each((element) => {
    u(element).handle('click', removeBedFormRow);
});
function removeBedFormRow(event) {
    let formRow = u(event.target).closest('.form-row');
    // hide table row
    formRow.addClass('hidden');
    // make the hidden DELETE field checked so the backend will delete the row when saving
    formRow.find('input[type="checkbox"]').attr('checked', 'checked');
    // update beds sum
    let bedSum = Number(u('#beds-sum').html());
    let value = Number(formRow.find('input[type="number"]').first().value);
    u('#beds-sum').html(bedSum - value);
}


/*
 * UPDATE BED SUM
 *
 * Every time the number of beds get changed, we want to update the corresponding bed sum.
 * This is achieved by storing the previous value on the focus event and calculating the difference on change.
 *
 */

// update previous value (for sum calculation)
u('.form-row').find('input[type="number"]').handle('focus', (event) => {
        u(event.target).data('previous', event.target.value);
});
// update previous values on page load
u(document).handle("DOMContentLoaded", () => {
    u('.form-row').find('input[type="number"]').trigger('focus');
});
// update sum value
u('.form-row').find('input[type="number"]').handle('change', updateBedSum);
function updateBedSum(event) {
    let bedSum = Number(u('#beds-sum').html());
    let previousValue = Number(u(event.target).data('previous'));
    let newValue = Number(event.target.value);
    u('#beds-sum').html(bedSum + newValue - previousValue);
    // set new previous value
    u(event.target).data('previous', newValue);
}

/*
 * DISABLE CHOSEN BED TARGET GROUP OPTIONS
 *
 * The following event handlers have the purpose to prevent it to select the same bed target group multiple times.
 * This is realized by disabling the chosen options for other select fields.
 * Every time a select field is changed, updateBedTargetGroupOptions() is executed which iterates over all select fields.
 * The current field is skipped, and then the previous value of the current field is enabled for other fields while the new value is disabled.
 * The previous value is stored on focus of the select fields.
 * This function is also executed on DOMContentLoaded because all options are enabled by default.
 *
 */

// update previous values
u('.form-row').each(function(element) {
    u(element).find('select').handle('focus', (event) => {
        u(event.target).data('previous', event.target.value);
    });
});
// update bed target group options on page load
u(document).handle("DOMContentLoaded", () => {
    u('.form-row').find('select').trigger('change');
});
// update bed target group options on change of the select box
u('.form-row').each(function(element) {
    u(element).find('select').handle('change', updateBedTargetGroupOptions);
});
function updateBedTargetGroupOptions(event) {
    let previousValue = parseInt(u(event.target).data('previous'));
    let newValue = parseInt(event.target.value);
    u('.form-row').each((row) => {
        if (event.target.isEqualNode(u(row).find('select').first())) {
            // skip for current select element
            return true;
        }
        // make previous option value enabled on other select fields
        if (!isNaN(previousValue)) {
            u(row).find('select').first().options[previousValue].disabled = false;
        }
        // make new option value disabled on other select fields
        if (!isNaN(newValue)) {
            u(row).find('select').first().options[newValue].disabled = true;
        }
    });
    // set new previous value
    u(event.target).data('previous', newValue);
}
