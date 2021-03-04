/*
 * The functionality to toggle subpages
 */

// event handler to hide and show subpages
u(".collapse-subpages").handle('click', toggle_subpages);

/*
 * This function toggles all subpages of the clicked page and changes the icon
 */
function toggle_subpages(event) {
    // Get span with all data options
    let collapse_span = u(event.target).closest("span");
    // Toggle subpages
    toggle_subpages_recursive(collapse_span);
    // Change icon
    let icon = u(collapse_span.children("svg").first());
    if (icon.hasClass('feather-chevron-down')) {
        collapse_span.html('<i data-feather="chevron-right"></i>');
    } else {
        collapse_span.html('<i data-feather="chevron-down"></i>');
    }
    // Trigger icon replacement
    feather.replace();
}

/*
 * This function iterates over all direct children of a page and
 * toggles their "hidden" class if they are not yet collapsed.
 * This enables to "save" the collapsed-state of all subpages, so when showing the subpages again,
 * all previously collapsed subpages will remain collapsed.
 */
function toggle_subpages_recursive(collapse_span) {
    // Get children of page
    let children = JSON.parse(collapse_span.data("page-children"));
    // Foreach child: toggle class "hidden" and proceed for all children which are not explicitly hidden themselves
    children.forEach(function (child_id) {
        // Get child table row
        let child = u("#page-" + child_id);
        // Hide/show table row
        child.toggleClass("hidden");
        // Remove the left sibling from possible drop targets while it is collapsed
        u("#page-" + child_id + "-drop-left").toggleClass("drop-between");
        // Find out whether this page has children itself
        let collapse_span = child.find(".collapse-subpages");
        // The icon will be null if the page is a leaf node
        let icon = u(collapse_span.children("svg").first());
        if (icon.hasClass('feather-chevron-down')) {
            // This means the children are not yet collapsed and have to be hidden as well
            toggle_subpages_recursive(collapse_span);
        }
    });
}
