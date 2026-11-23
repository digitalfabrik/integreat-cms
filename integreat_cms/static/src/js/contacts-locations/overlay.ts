/*
 * PROTOTYPE: open and close the card overlays (native <dialog> elements) of the contacts & locations page
 */

document.addEventListener("click", ({ target }) => {
    const element = target as HTMLElement;
    const opener = element.closest("[data-overlay-open]");
    if (opener) {
        document.querySelector<HTMLDialogElement>(`#${opener.getAttribute("data-overlay-open")}`)?.showModal();
        return;
    }
    // A click on the backdrop targets the dialog element itself
    if (element.closest("[data-overlay-close]") || element.matches("dialog[data-overlay]")) {
        element.closest<HTMLDialogElement>("dialog[data-overlay]")?.close();
        return;
    }
    // "Anwenden" in the category multiselect: just close the dropdown, the checkboxes are already set
    const detailsCloser = element.closest("[data-details-close]");
    if (detailsCloser) {
        detailsCloser.closest("details")?.removeAttribute("open");
        return;
    }
    // "Verknüpfung entfernen" on the place edit page: hide the row, it is back after a reload
    const remover = element.closest("[data-remove-row]");
    if (remover) {
        remover.closest("[data-removable-row]")?.remove();
        return;
    }
    // Place dropdown: picking a place shows it in the closed dropdown
    const option = element.closest("[data-place-picker-option]");
    if (option) {
        const picker = option.closest<HTMLDetailsElement>("[data-place-picker]");
        const value = picker.querySelector("[data-place-picker-value]");
        value.textContent = option.querySelector("span").textContent;
        value.classList.remove("opacity-60");
        picker.querySelector<HTMLInputElement>("[data-place-picker-input]").value = option.getAttribute("data-place-id");
        picker.open = false;
    }
});

// Place dropdown: filter the places while typing in the search field
document.addEventListener("input", ({ target }) => {
    const search = (target as HTMLElement).closest<HTMLInputElement>("[data-place-picker-search]");
    if (!search) {
        return;
    }
    const picker = search.closest("[data-place-picker]");
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    picker.querySelectorAll<HTMLElement>("[data-place-picker-option]").forEach((option) => {
        const match = option.textContent.toLowerCase().includes(query);
        option.classList.toggle("hidden", !match);
        visible += match ? 1 : 0;
    });
    picker.querySelector("[data-place-picker-empty]").classList.toggle("hidden", visible > 0);
});

// Place dropdown: focus the search field when the dropdown opens
document.addEventListener(
    "toggle",
    ({ target }) => {
        const picker = target as HTMLDetailsElement;
        if (picker.matches?.("[data-place-picker]") && picker.open) {
            picker.querySelector<HTMLInputElement>("[data-place-picker-search]").focus();
        }
    },
    // The toggle event does not bubble, so listen in the capture phase
    true
);

// Browser back may show a cached copy of a prototype page without the new place/contact, so reload it then
window.addEventListener("pageshow", (event) => {
    if (event.persisted && window.location.pathname.includes("/contacts-locations/")) {
        window.location.reload();
    }
});
