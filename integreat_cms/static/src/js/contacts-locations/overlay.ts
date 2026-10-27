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
    }
});
