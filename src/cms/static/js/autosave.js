async function autosave_editor(event){
    const data = await fetch(window.location, {method: 'POST', headers: { "X-CSRFToken": u('#content_form').find('input[name=csrfmiddlewaretoken]').first().value, "Content-Type": "application/x-www-form-urlencoded"}, body: u('#content_form').serialize()});
}
