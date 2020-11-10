/**
 * Handles the checkbox for selecting and unselecting all pages.
 */
function select_all_pages() {
    var selected_pages = document.getElementsByName("page_selected");
    if (document.getElementsByName("select_all_pages")[0].checked == true) {
        selected_pages.forEach(e => e.checked = true);
    } else {
        selected_pages.forEach(e => e.checked = false);
    }
}

/**
 * Handles bulk action execution depending on the selected action.
 * In general the selected pages get retrieved and forwarded to the django view
 * that corresponds to the selected action.
 */
function bulk_action_execute() {
    var action = document.getElementById('bulk_action').value;
    // match action types
    if ( action == "archive_pages" ) {
        // TODO
    } else if (action == "pdf_export") {
        var selected_pages = document.getElementsByName("page_selected");
        pages = [];
        selected_pages.forEach(e => {
            if(e.checked) {
                pages.push(e.value)
            }
        })
        if (pages.length != 0) {
            var pdf_export_url = document.getElementById("pdf_export_url").value;
            window.open(pdf_export_url+"?pages="+pages.join(','));
        } 
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
