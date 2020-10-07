/**
 * This file contains all functions which are needed for the bulk actions for pages.
 */

function select_all_pages() {
    var selected_pages = document.getElementsByName("page_selected");
    if (document.getElementsByName("select_all_pages")[0].checked == true) {
        selected_pages.forEach(e => e.checked = true);
    } else {
        selected_pages.forEach(e => e.checked = false);
    }
}

function bulk_action_execute() {
    var action = document.getElementById('bulk_action').value;
    // match action types
    if ( action == "archive_pages" ) {
        // TODO
    } else if ( action == 'pdf_export') {
        u()
    } else { // no previous match, than language code -> XLIFF export
        var page_selected = document.getElementsByName("page_selected");
        var pages = [];
        page_selected.forEach(async function (page_checkbox) {
            if(page_checkbox.checked) {
                pages = pages.concat(page_checkbox.value);
            }
        });
        if (pages.length == 0) {
            return;
        }
        var bulk_action_url = document.getElementById("bulk_action_url").value;
        window.open(bulk_action_url+"?target_lang="+action+"&pages="+pages.join(','), "_blank");
    }
}
