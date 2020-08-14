u(document).handle('DOMContentLoaded', set_poi_query_event_listeners);

async function query_pois(url, query_string, region_slug, create_poi_option) {
    const data = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': u('[name=csrfmiddlewaretoken]').first().value
        },
        body: JSON.stringify({
            'query_string': query_string,
            'region_slug': region_slug,
            'create_poi_option': create_poi_option
        })
    }).then(res => {
        if (res.status != 200) {
            // Invalid status => return empty result
            return '';
        } else {
            // Return response text
            return res.text();
        }
    });
    if (data) {
        // Set and display new data
        u('#poi-query-result').removeClass('hidden');
        u('#poi-query-result').html(data);
    }

    u('.option-new-poi').each(function (node) {
        u(node).handle('click', new_poi_window);
    });

    u('.option-existing-poi').each(function (node) {
        u(node).handle('click', set_poi);
    });
}

function set_poi(event) {
    let option = u(event.target).closest('.option-existing-poi');
    render_poi_data(
        option.data('poi-title'),
        option.data('poi-id'),
        option.data('poi-address'),
        option.data('poi-city'),
        option.data('poi-country')
    );
}

function remove_poi() {
    render_poi_data(
        u('#poi-query-input').data('default-placeholder'),
        -1,
        '',
        '',
        ''
    );
}

function new_poi_window(event) {
    let option = u(event.target).closest('.option-new-poi');
    let new_window = window.open(option.data('url'), "_blank");
    new_window.onload = function () {
        u('#id_title', new_window.document).attr('value', option.data('poi-title'));
    }
}

function render_poi_data(query_placeholder, id, address, city, country) {
    u('#poi-query-input').attr('placeholder', query_placeholder);
    u('#poi-id').attr('value', id);
    u('#poi-address').attr('value', address);
    u('#poi-city').attr('value', city);
    u('#poi-country').attr('value', country);

    u('#poi-query-result').addClass('hidden');
    u('#poi-query-input').first().value = '';
}

function set_poi_query_event_listeners() {
    let scheduled_function = false;
    // AJAX search
    u('#poi-query-input').handle('keyup', function (event) {
        let input_field = u(event.target).closest('input');

        // Reschedule function execution on new input
        if (scheduled_function) {
            clearTimeout(scheduled_function);
        }
        // Schedule function execution
        scheduled_function = setTimeout(
            query_pois,
            300,
            input_field.data('url'),
            input_field.first().value,
            input_field.data('region-slug'),
            !input_field.hasClass('no-new-poi')  // Allow suppressing the option to create a new POI
        );
    });

    // Hide AJAX search results
    u(document).on('click', function (event) {
        if (
            u(event.target).closest('#poi-query-input').first() !== u('#poi-query-input').first() &&
            u(event.target).closest('#poi-query-result').first() !== u('#poi-query-result').first()
        ) {
            // Neither clicking on input field nor on result to select it
            u('#poi-query-result').empty();
            u('#poi-query-input').first().value = '';
        }
    });

    // Remove POI
    u('#poi-remove').handle('click', remove_poi);
}
