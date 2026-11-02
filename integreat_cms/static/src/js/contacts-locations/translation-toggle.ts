/*
 * PROTOTYPE: the "zeige Übersetzungsdetails" switch swaps the places table for the translation view without reload
 */

document.addEventListener("change", ({ target }) => {
    const toggle = (target as HTMLElement).closest<HTMLInputElement>("[data-translation-toggle]");
    if (!toggle) {
        return;
    }
    document.querySelectorAll<HTMLElement>("[data-translation-view]").forEach((view) => {
        view.classList.toggle("hidden", view.getAttribute("data-translation-view") !== (toggle.checked ? "on" : "off"));
    });
});
