u(document).handle('DOMContentLoaded', set_poi_query_event_listeners);

async function query_pois(url, query_string, region_slug, language_code) {
    const data = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': u('[name=csrfmiddlewaretoken]').first().value
        },
        body: JSON.stringify({
            'query_string': query_string,
            'region_slug': region_slug,
            'language_code': language_code
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
        u('#poi-query-result').first().classList.remove('hidden');
        u('#poi-query-result').html(data);
    }

    u('.option-new-poi').each(function (node, i) {
        u(node).handle('click', () => console.log('Clicked on new node ' + i));
    });

    u('.option-existing-poi').each(function (node) {
        u(node).handle('click', set_poi);
    });
}

function set_poi(event) {
    let option = u(event.target).closest('option');
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

function render_poi_data(query_placeholder, id, address, city, country) {
    u('#poi-query-input').attr('placeholder', query_placeholder);
    u('#poi-id').attr('value', id);
    u('#poi-address').attr('value', address);
    u('#poi-city').attr('value', city);
    u('#poi-country').attr('value', country);

    u('#poi-query-result').first().classList.add('hidden');
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
            input_field.data('language-code')
        );
    });

    // Hide AJAX search results
    u(document).on('click', function (event) {
        if (
            u(event.target).closest('#poi-query-input').first() !== u('#poi-query-input').first() &&
            u(event.target).closest('#poi-query-result').first() !== u('#poi-query-result').first()
        ) {
            // Neither clicking on input field nor on result to select it
            u('#poi-query-result').first().classList.add('hidden');
            u('#poi-query-input').first().value = '';
        }
    });

    // Remove POI
    u('#poi-remove').on('click', function (event) {
        event.preventDefault();
        remove_poi();
    });
}