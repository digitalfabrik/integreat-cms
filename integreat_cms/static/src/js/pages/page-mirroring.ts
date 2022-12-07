/**
 * This file contains all functions which are needed for embedding live content aka page mirroring.
 */

const renderMirroredPageField = ({ target }: Event) => {
    // Check if a region was selected
    if ((target as HTMLInputElement).value === "") {
        // Remove mirrored page field to make sure no old value is selected
        document.getElementById("mirrored_page_div").innerHTML = "";
        // Hide fields
        document.getElementById("mirrored_page_div").classList.add("hidden");
        document.getElementById("mirrored_page_first_div").classList.add("hidden");
    } else {
        // Fetch rendered mirrored page field for selected region
        fetch(
            document.getElementById("mirrored_page_div").getAttribute("data-url") + (target as HTMLInputElement).value
        )
            .then((response) => {
                if (response.ok) {
                    return response.text();
                }
                throw new Error(response.statusText);
            })
            .then((html) => {
                // Load rendered field into div and show it
                document.getElementById("mirrored_page_div").innerHTML = html;
                document.getElementById("mirrored_page_div").classList.remove("hidden");
                document.getElementById("mirrored_page_first_div").classList.remove("hidden");
            })
            .catch((error) => {
                // Show error message instead of field
                document.getElementById("mirrored_page_div").innerHTML =
                    '<div class="bg-red-100 border-l-4 border-red-500 text-red-500 px-4 py-3 my-4" role="alert"><p id="mirrored-page-error"></p></div>';
                document.getElementById("mirrored-page-error").innerText = error.message;
                document.getElementById("mirrored_page_div").classList.remove("hidden");
                document.getElementById("mirrored_page_first_div").classList.add("hidden");
            });
    }
};

window.addEventListener("load", () => {
    // Event handler for rendering the mirrored page field
    const mirroredRegion = document.getElementById("mirrored_page_region");
    if (mirroredRegion) {
        mirroredRegion.addEventListener("change", renderMirroredPageField);
    }
});
