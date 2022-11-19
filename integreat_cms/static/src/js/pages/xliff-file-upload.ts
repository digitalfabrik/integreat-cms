/*
 * This file contains all functions used for the XLIFF import
 */

/**
 * Listen for user input (selection in file browser) for uploading XLIFF files.
 * Updates the UI for submitting.
 *
 * @param {target} eventTarget - The changed file input
 */
const selectXliffFile = ({ target }: Event) => {
    const { files } = target as HTMLInputElement;
    // Update xliff file label
    const label = document.querySelector("#xliff_file_label");
    label.classList.remove("bg-blue-500", "hover:bg-blue-600");
    label.classList.add("bg-gray-500", "hover:bg-gray-600");
    label.textContent = files[0].name;
    if (files.length > 1) {
        // Get translated text for "and {} other files"
        const labelMultiple = document.querySelector("#xliff_file_label_multiple");
        label.textContent += labelMultiple.textContent.replace("{}", (files.length - 1).toString());
    }
    // Update xliff file submit button
    const submitButton = document.querySelector("#xliff_file_submit") as HTMLInputElement;
    submitButton.disabled = false;
};

// Set event handler
window.addEventListener("load", () => {
    // Event handler for changing the parent page option
    document.getElementById("xliff_file")?.addEventListener("change", selectXliffFile);
});
