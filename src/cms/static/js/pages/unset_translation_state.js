/*
These functions get triggered when user reset the currently_in_translation state
ajax POST request for database update is send, update of translation state icons accordingly
*/
function unset_translation_state(pageId, languageCode) {
    // fetch url from template
    const url = u("#undo-translation").first().dataset.url;
    const translationState = false;
    // send ajax request for database update
    post_translation_state(url, pageId, languageCode, translationState)
    // on success update GUI
    .then(response => update_translation_form(response));
}

/*
sends ajax request for updating all pages 
to the given translationState
*/
async function post_translation_state(url, pageId, languageCode, translationState) {
    const data = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
            'X-CSRFToken': u('[name=csrfmiddlewaretoken]').first().value
        },
        body: JSON.stringify({
            'language': languageCode,
            'pageId': pageId,
            'translationState': translationState
        })
    }).then(response => response.json());
    return data;
}

function update_translation_form(data) {
    /* the icons representing the state of the translation 
    depend on template context at the moment the form was called
    so to update the GUI state, initial state gets hidden and current state is displayed */
    let translationTab = u(`.${data["language"]}`);
    translationTab.addClass("hidden");
    translationTab.siblings(".ajax").removeClass("hidden");
    u("#trans-warn").addClass("hidden");
}