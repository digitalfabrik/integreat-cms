/**
 * This file contains all functions which are needed for embedding live content aka page mirroring.
 */

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
