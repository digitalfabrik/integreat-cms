/**
 * This file contains all event handlers and functions which are needed for granting and revoking permissions on individual pages.
 */

u(document).handle('DOMContentLoaded', set_page_permission_event_listeners);

// function to set the page permission event listeners
function set_page_permission_event_listeners() {

    u('.grant-page-permission').each(function(node)  {
        u(node).handle('click', grant_page_permission);
    });
    u('.revoke-page-permission').each(function(node)  {
        u(node).handle('click', revoke_page_permission);
    });

}

// function for granting page permissions
async function grant_page_permission(event) {
    let button = u(event.target).closest('button');
    let user_id = button.parent().find('select').first().value;
    // only submit ajax request when user is selected
    if (user_id) {
        await update_page_permission(
            button.data('url'),
            button.data('page-id'),
            user_id,
            button.data('permission'),
        );
    }
}

// function for revoking page permissions
async function revoke_page_permission(event) {
    let link = u(event.target).closest('a');
    await update_page_permission(
        link.attr('href'),
        link.data('page-id'),
        link.data('user-id'),
        link.data('permission')
    );
}

// ajax call for updating the page permissions
async function update_page_permission(url, page_id, user_id, permission) {
    const data = await fetch(url, {
        method: 'POST',
        headers:  {
            'X-CSRFToken': u('[name=csrfmiddlewaretoken]').first().value
        },
        body: JSON.stringify({
            'page_id': page_id,
            'user_id': user_id,
            'permission': permission
        })
    }).then(res => {
        if (res.status !== 200) {
            // return empty result if status is not ok
            return '';
        } else {
            // return response text otherwise
            return res.text();
        }
    });
    if (data) {
        // insert response into table
        u("#page_permission_table").html(data);
        // set new event listeners
        set_page_permission_event_listeners();
        // trigger icon replacement
        feather.replace();
    }

}
