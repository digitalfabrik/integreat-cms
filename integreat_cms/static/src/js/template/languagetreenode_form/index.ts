/**
 *
 * used in:
 * languagetreenode_form.html
 * maybe others?
 */
window.addEventListener("load", () => {
    const warningDiv = document.getElementById("visible-warning") as HTMLDivElement;
    const activeCheckbox = document.getElementById("id_active") as HTMLInputElement;
    const visibleCheckbox = document.getElementById("id_visible") as HTMLInputElement;

    const toggleCheckbox = (languageIsActive: boolean) => {
        if (languageIsActive) {
            visibleCheckbox.disabled = false;
            warningDiv.classList.toggle("hidden", true);
        } else {
            warningDiv.classList.toggle("hidden", false);
            visibleCheckbox.disabled = true;
            visibleCheckbox.checked = false;
        }
    };

    if (warningDiv && activeCheckbox && visibleCheckbox) {
        toggleCheckbox(activeCheckbox.checked);

        activeCheckbox.addEventListener("change", () => {
            toggleCheckbox(activeCheckbox.checked);
        });
    }
});
