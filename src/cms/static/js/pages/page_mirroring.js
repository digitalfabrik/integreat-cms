/**
 * This file contains all functions which are needed for embedding live content aka page mirroring.
 */

// Event handler for rendering the mirrored page field
u('#mirrored_page_region').on('change', render_mirrored_page_field);

function render_mirrored_page_field(event){
    // Check if a region was selected
    if(event.target.value === "") {
        // Remove mirrored page field to make sure no old value is selected
        u('#mirrored_page_div').html("");
        // Hide fields
        u('#mirrored_page_div').addClass('hidden');
        u('#mirrored_page_first_div').addClass('hidden');
    } else {
        // Fetch rendered mirrored page field for selected region
        fetch(u('#mirrored_page_div').data('url') + event.target.value).then(function (response) {
            if (response.ok) {
              return response.text();
            }
            throw new Error(response.statusText);
        }).then(function (html) {
            // Load rendered field into div and show it
            u('#mirrored_page_div').html(html);
            u('#mirrored_page_div').removeClass('hidden');
            u('#mirrored_page_first_div').removeClass('hidden');
        }).catch(function (error) {
            // Show error message instead of field
            u('#mirrored_page_div').html('<div class="bg-red-100 border-l-4 border-red-500 text-red-500 px-4 py-3 my-4" role="alert"><p>' + error.message + '</p></div>');
            u('#mirrored_page_div').removeClass('hidden');
            u('#mirrored_page_first_div').addClass('hidden');
        });
    }
}
