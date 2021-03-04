// Event handler for changing the parent page option
u('#parent').on('change', get_page_order_table);

// This function updates the page order table each time the parent select changes
function get_page_order_table(event) {
    // Get selected option node
    let selected_option = u('#parent').children('option[value="' + event.target.value + '"]');
    // Fetch page order table
    fetch(selected_option.data('url')).then(function (response) {
        if (response.ok) {
            return response.text();
        }
        throw new Error(response.statusText);
    }).then(function (html) {
        // Load new page order table
        u('#page_order_table').html(html);
        // Check if the page is part of the parent's children
        let page_contained_in_siblings = u('.drag').data('contained-in-siblings');
        if (page_contained_in_siblings) {
            // Reset hidden field values to default value
            u('#id_related_page').attr('value', u('#id_related_page').first().defaultValue);
            u('#id_position').attr('value', u('#id_position').first().defaultValue);
        } else {
            // Change hidden field values to last child of parent
            u('#id_related_page').attr('value', event.target.value);
            u('#id_position').attr('value', 'last-child');
        }
        // Update the modified page title
        update_page_title();
        // Trigger icon replacement
        feather.replace();
        // Register event handlers
        register_event_handlers();
    }).catch(function (error) {
        // Show error message instead of table
        u('#page_order_table').html('<div class="bg-red-100 border-l-4 border-red-500 text-red-500 px-4 py-3 my-4" role="alert"><p>' + error.message + '</p></div>');
    });
}

// Event handler for updating the page title
u('#id_title').on('input', update_page_title);

// save initial page title
const initial_page_title = u('#id_title').first().value;

// This function inserts the updated page title in the page order table
function update_page_title() {
    let page_title = u('#id_title').first().value;
    if (page_title == "" || page_title == initial_page_title) {
        page_title = u('#page_title').data('default-title');
    }
    u('#page_title').html(page_title);
}

// Function for registering all event handlers for drag/drop events
function register_event_handlers() {
    // At first, reset all existing handlers
    u('.drop').each(function(node) {
        u(node).off('dragleave,dragover,drop');
    });
    // Event handlers for drag events (delay because of behaviour in Chrome browser)
    u('.drag').on('dragstart', function(event) {
        window.setTimeout(dragstart, 0, event);
    });
    u('.drag').handle('dragend', dragend);
    // Event handlers for drop events
    u('.drop').each(function(node) {
        u(node).handle('dragover', dragover);
        u(node).handle('dragleave', dragleave);
        u(node).handle('drop', drop);
    });
}

// Register all handlers once initially
register_event_handlers();

/*
 * This function handles the start of a dragging event
 *
 * Manipulating the dom during dragstart event fires immediately a dragend event (chrome browser),
 * so the changes to the dom must be delayed
 */
function dragstart(event) {
    // change appearance of dragged item
    u(event.target).removeClass('text-gray-800');
    u(event.target).addClass('text-blue-500');
    // show dropping regions between table rows
    u('.drop-between').each(function(node)  {
        u(node).closest('tr').removeClass("hidden");
    });
}

// This function adds the hover effect when the dragged page is hovered over a valid drop region
function dragover(event) {
    u(event.target.parentElement).closest('tr').addClass("drop-allow");
}

// This function handles the event that the drag stops, no matter if on a valid drop region or not
function dragend(event) {
    // Hide the drop regions between table rows
    u('.drop-between').each(function(node) {
        u(node).closest('tr').addClass("hidden");
    });
    // Change appearance of dragged item
    u(event.target).removeClass('text-blue-500');
    u(event.target).addClass('text-gray-800');
}

// This function handles the event then the cursor leaves a drop region without actually dropping
function dragleave(event) {
    // Remove hover effect on allowed or disallowed drop regions
    var target = u(event.target.parentElement).closest('tr');
    target.removeClass("drop-allow");
}

// This function handles the event when the page is dropped onto the target div
function drop(event) {
    // Get the table row which was dragged
    let dragged_page = u('.drag').closest('tr');
    // Get the table row onto which the page was dropped
    let target = u(event.target.parentElement).closest('tr');
    // Insert the page before the drop target
    target.before(dragged_page);
    // Remove the page from its original position
    dragged_page.remove()
    // Toggle classes to deactivate the drop region where the dragged page was dropped
    target.toggleClass('drop drop-deactivated drop-between drop-between-deactivated');
    // Remove the drop-allow class which creates the hover effect (blue line)
    target.removeClass('drop-allow');
    // Toggle classes to activate the previously deactivated drop regions
    u('.drop-deactivated').toggleClass('drop drop-deactivated');
    u('.drop-between-deactivated').toggleClass('drop-between drop-between-deactivated');
    // Read form field values from data attributes
    let target_id = target.attr("data-drop-id");
    let position = target.attr("data-drop-position");
    // Passing the values to the hidden fields
    u('#id_related_page').attr('value', target.data('drop-id'));
    u('#id_position').attr('value', target.data('drop-position'));
    // Register new event handlers
    register_event_handlers();
}
