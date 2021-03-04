/**
 * This file contains all functions which are needed for the bulk actions.
 *
 * Usage:
 *
 *  TEMPLATE
 * ##########
 *
 * - Add <form> around list/table
 * - Add <input type="checkbox" id="bulk-select-all"> in table head
 * - Add <input type="checkbox" name="selected_ids[]" value="{{ item.id }}" class="bulk-select-item"> in each table row
 * - Add options for all bulk actions
 *
 *         <select id="bulk-action">
 *             <option>{% trans 'Select bulk action' %}</option>
 *             <option data-bulk-action="{% url 'option_url' %}">{% trans 'Option' %}</option>
 *             <option data-bulk-action="{% url 'option_url' %}" data-target="_blank">{% trans 'Option opened in new tab' %}</option>
 *         </select>
 *
 * - Add submit button: <input id="bulk-action-execute" type="submit" value="{% trans 'Execute' %}" />
 * - Include <script src="{% static 'js/bulk_actions.js' %}"></script> in javascript block
 *
 *  VIEW
 * ######
 *
 * Retrieve the selected page ids like this:
 *
 *     page_ids = request.POST.getlist("selected_ids[]")
 *
 */

u("#bulk-select-all").on("click", bulk_select_all);
function bulk_select_all() {
    u(".bulk-select-item").each(function(item){
        // Set the "checked" attr of all items to the "checked" state of the top checkbox
        item.checked = u("#bulk-select-all").first().checked;
    });
}

toggle_bulk_action_button();
u(".bulk-select-item").on("click", toggle_bulk_action_button);
u("#bulk-select-all").on("click", toggle_bulk_action_button);
u("#bulk-action").on("change", toggle_bulk_action_button);
function toggle_bulk_action_button() {
    let bulk_action_button = u("#bulk-action-execute")
    // Only activate button if at least one item and the action is selected
    if (u(".bulk-select-item").filter(":checked").length === 0 || u("#bulk-action").first().selectedIndex === 0) {
        bulk_action_button.removeClass("bg-blue-500", "hover:bg-blue-600", "cursor-pointer");
        bulk_action_button.addClass("bg-gray-500", "cursor-not-allowed");
        bulk_action_button.first().disabled = true;
    } else  {
        bulk_action_button.removeClass("bg-gray-500", "cursor-not-allowed");
        bulk_action_button.addClass("bg-blue-500", "hover:bg-blue-600", "cursor-pointer");
        bulk_action_button.first().disabled = false;
    }
}

u("#bulk-action-form").handle('submit', bulk_action_execute);
function bulk_action_execute(event) {
    let select = u("#bulk-action").first();
    let selected_action = u(select.options[select.selectedIndex]);
    // Set form action to url of the bulk action
    event.target.action = selected_action.data("bulk-action");
    // Set form target in case action is to be opened in a new tab
    let target = selected_action.data("target");
    if (target !== null) {
        event.target.target = target;
    }
    // Submit form and execute bulk action
    event.target.submit();
}
