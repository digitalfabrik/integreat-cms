const query_input = u('#poi-query-input');
const query_result = u('#poi-query-result');
const delay_in_ms = 700;
let scheduled_function = false;

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
        query_result.first().classList.remove('hidden');
        query_result.html(data);
    }
}

function set_poi_query_event_listeners() {
    // AJAX search
    query_input.handle('keyup', function (event) {
        let input_field = u(event.target).closest('input');

        // Reschedule function execution on new input
        if (scheduled_function) {
            clearTimeout(scheduled_function);
        }
        // Schedule function execution
        scheduled_function = setTimeout(
            query_pois,
            delay_in_ms,
            input_field.data('url'),
            input_field.first().value,
            input_field.data('region-slug'),
            input_field.data('language-code')
        );
    });

    // Hide AJAX search results
    u(document).handle('click', function (event) {
        if (
            u(event.target).closest('#poi-query-input').first() !== query_input.first() &&
            u(event.target).closest('#poi-query-result').first() !== query_result.first()
        ) {
            // Neither clicking on input field nor on result to select it
            query_result.first().classList.add('hidden');
            query_input.first().value = '';
        }
    });
}