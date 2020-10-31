/**
 * This file contains all event handlers and functions which are needed for drag & drop functionality in trees.
 * Currently, this is used in src/cms/templates/pages/page_tree.html and src/cms/templates/language_tree/language_tree.html
 */

// event handler for starting drag events
u('.drag').each(function(node) {
    u(node).on('dragstart', dragstart);
});
function dragstart(event) {
    // prepare the dragged node id for data transfer
    event.dataTransfer.setData("text", u(event.target).attr("data-drag-id"));
    window.setTimeout(change_dom, 50, event.target);
    // get descendants of dragged node
    var descendants = JSON.parse(u(event.target).attr("data-node-descendants"));
    // add event listeners for hovering over drop regions
    u('.drop').each(function(node) {
        // get target node id of the hovered drop region
        var drop_id = parseInt(u(node).attr("data-drop-id"));
        if (descendants.includes(drop_id)) {
            // if the target node is a descendant of the dragged node, disallow dropping it
            u(node).on('dragover', drop_disallow);
        } else {
            // else, the move would be valid and dropping is allowed
            u(node).handle('dragover', drop_allow);
        }
    });
}

/* manipulating the dom during dragstart event fires immediately a dragend event (chrome browser)
so the changes to the dom must be delayed */
function change_dom(target) {
    // change appearance of dragged item
    u(target).removeClass('text-gray-800');
    u(target).addClass('text-blue-500');
    // show dropping regions between table rows
    u('.drop-between').each(function(node)  {
        u(node).closest('tr').removeClass("hidden");
    });
}

// event handlers for dragover events
function drop_allow(event) {
    u(event.target.parentElement).closest('tr').addClass("drop-allow");
}
function drop_disallow(event) {
    u(event.target.parentElement).closest('tr').addClass("drop-disallow");
}

// event handler for stopping drag events
u('.drag').each(function(node) {
    u(node).handle('dragend', dragend);
});
function dragend(event) {
    // hide the drop regions between table rows
    u('.drop-between').each(function(node) {
        u(node).closest('tr').addClass("hidden");
    });
    // remove event listeners for dragover events
    u('.drop').each(function(node) {
        u(node).off('dragover');
    });
    // change appearance of dragged item
    u(event.target).removeClass('text-blue-500');
    u(event.target).addClass('text-gray-800');
}

// event handler for dragleave events
u('.drop').each(function(node) {
    u(node).handle('dragleave', dragleave);
});
function dragleave(event) {
    // remove hover effect on allowed or disallowed drop regions
    var target = u(event.target.parentElement).closest('tr');
    target.removeClass("drop-allow");
    target.removeClass("drop-disallow");
}

// event handler for drop events
u('.drop').each(function(node) {
    u(node).handle('drop', drop);
});
function drop(event) {
    // prevent the table from collapsing again after successful drop
    u('.drag').each(function(node) {
        u(node).off('dragend');
    });
    // get dragged node id from data transfer
    var node_id = event.dataTransfer.getData("text");
    // get target node if from dropped region
    var target = u(event.target.parentElement).closest('tr');
    var target_id = target.attr("data-drop-id");
    var position = target.attr("data-drop-position");
    // call view to move a node (current location is the nodes url)
    window.location.href = window.location.href + node_id + "/move/" + target_id + "/" + position;
}
