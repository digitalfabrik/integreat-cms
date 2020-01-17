/* start page mirroring */

async function update_mirrored_pages_list(url, page_id, selected=""){
  if(u("#mirrored_page_region").first().value === "") {
    u('#mirrored_page_div').addClass('hidden');
    u('#mirrored_page_first_div').addClass('hidden');
  }
  const data = await fetch(url, {
    method: 'POST',
    headers:  {
      'X-CSRFToken': u('[name=csrfmiddlewaretoken]').first().value
    },
    body: JSON.stringify({
      "region": u("#mirrored_page_region").first().value,
      "current_page": page_id,
    })
  }).then(res => {
    if (res.status != 200) {
      return '';
    } else {
      return res.text();
    }
  });
  if (data) {
    u('#mirrored_page').html("<option value=''>------</option>")
    var data2 = JSON.parse(data)
    if(data2['nolist'] == true) {
      return;
    }
    data2.sort(function (a, b) {
      return a.name.localeCompare(b.name);
    });
    for (var key in data2) {
      var option = document.createElement("option");
      option.text = data2[key]['name'];
      option.value = data2[key]['id'];
      u('#mirrored_page').append(option);
    }
    document.getElementById('mirrored_page').value=selected;
    u('#mirrored_page_div').removeClass('hidden');
    u('#mirrored_page_first_div').removeClass('hidden');
  }
}

async function save_mirrored_page(url, page_id){
  if((u("#mirrored_page_region").first().value === "") || (u("#mirrored_page").first().value === "")) {
    var mirrored_page = "0";
  } else {
    var mirrored_page = u("#mirrored_page").first().value;
  }
  const data = await fetch(url, {
    method: 'POST',
    headers:  {
      'X-CSRFToken': u('[name=csrfmiddlewaretoken]').first().value
    },
    body: JSON.stringify({
      "mirrored_page": mirrored_page,
      "mirrored_page_first": u("#mirrored_page_first").first().value,
      "current_page": page_id,
    })
  }).then(res => {
    if (res.status != 200) {
      return '';
    } else {
      return res.text();
    }
  });
}

/* end page mirroring */

/* start page permissions */

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

/* end page permissions */
