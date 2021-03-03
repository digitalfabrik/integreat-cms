/* this file updates the permalink of the current page form
when the user edited the page translations title */

document.getElementById("id_title").addEventListener("focusout", function(e){
    let currentTitle = e.target.value;
    let url = document.querySelector('[for="id_title"]').dataset.slugifyUrl;
    slugify(url, {"title": currentTitle})
        .then(response => {
        document.getElementById('id_slug').setAttribute("value", response["unique_slug"]);
        });
});

async function slugify(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
            'X-CSRFToken': document.getElementsByName('csrfmiddlewaretoken')[0].value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    return response;
}
