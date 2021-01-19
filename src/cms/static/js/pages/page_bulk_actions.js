/**
 * This file contains all functions which are needed for the bulk actions for pages.
 */

u(document).on('DOMContentLoaded', function () {
    
    u('[name="select_all_pages"]').on('click', select_all_pages);
    function select_all_pages() {
        var selected_pages = document.getElementsByName("page_selected");
        if (document.getElementsByName("select_all_pages")[0].checked == true) {
            selected_pages.forEach(e => e.checked = true);
        } else {
            selected_pages.forEach(e => e.checked = false);
        }
    }

    u("#bulk_action_btn").on('click', bulk_action_execute);
    function bulk_action_execute() {
        var action = u('#bulk_action').first().value;
        var pages = [];
        u('input').filter(':checked').each((node, i) => pages.push(node.value));
        if (pages.length == 0) {
            // abort if no pages selected
            return;
        }
        // match action types
        if ( action == "archive_pages" ) {
            // TODO
        } else if (action == "pdf_export") {
            var pdf_export_url = document.getElementById("pdf_export_url").value;
            window.open(pdf_export_url+"?pages="+pages.join(','));
        } else { // no previous match, than language code -> XLIFF export
            const state = true;
            const url = u("#ajax_url").first().dataset.url;
            var bulk_action_url = document.getElementById("bulk_action_url").value;
            // download XLIFF
            window.open(bulk_action_url+"?target_lang="+action+"&pages="+pages.join(','), "_blank");
            updateTranslationIcon(pages, action);
        }
    }

    function updateTranslationIcon(pages, languageCode) {
        for (page of pages){
            let pageNode = u(`#page-${page}`);
            // get language for updating translation state icon
            let targetLanguage = pageNode.find(`.${languageCode}`);
            if (!targetLanguage.find("#translation-icon").find("span").hasClass("no-trans")) {
                // if the page already contains a translation for the exported language
                // hide inital translation state determind by templates context
                targetLanguage.find("#translation-icon").addClass("hidden");
                targetLanguage.find("#ajax-icon").removeClass("hidden");
                // notify user that update was successful by setting right icon
                pageNode.find(".translation-title").addClass("hidden");
                pageNode.find(".ajax-title").removeClass("hidden");
            }
        }
    }
    
});
