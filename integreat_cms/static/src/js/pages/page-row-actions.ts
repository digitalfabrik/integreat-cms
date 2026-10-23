/*
 * The functionality to open and close the "more actions" menu of the page tree rows
 */

const MENU_OFFSET = 4;

const setMenuOpen = (wrapper: Element, open: boolean) => {
    const menu = wrapper.querySelector("[data-row-actions-menu]");
    // The menu is displayed as flex container, so both classes have to be toggled
    menu?.classList.toggle("hidden", !open);
    menu?.classList.toggle("flex", open);
    wrapper.querySelector("[data-row-actions-toggle]")?.setAttribute("aria-expanded", String(open));
};

const closeAllMenus = () => {
    document.querySelectorAll("[data-row-actions]").forEach((wrapper) => setMenuOpen(wrapper, false));
};

/**
 * The menu is positioned fixed because the table is wrapped in a scroll container which would clip it.
 * It is aligned with the right edge of the toggle button and opens upwards if there is not enough space below.
 *
 * @param wrapper The wrapper element of the toggle button and the menu
 */
const openMenu = (wrapper: Element) => {
    const toggle = wrapper.querySelector("[data-row-actions-toggle]");
    const menu = wrapper.querySelector<HTMLElement>("[data-row-actions-menu]");
    setMenuOpen(wrapper, true);
    const toggleRect = toggle.getBoundingClientRect();
    const menuRect = menu.getBoundingClientRect();
    const fitsBelow = toggleRect.bottom + MENU_OFFSET + menuRect.height <= window.innerHeight;
    const top = fitsBelow ? toggleRect.bottom + MENU_OFFSET : toggleRect.top - MENU_OFFSET - menuRect.height;
    menu.style.top = `${Math.max(0, top)}px`;
    menu.style.left = `${Math.max(0, toggleRect.right - menuRect.width)}px`;
};

// The listeners are attached to the document, so rows which are loaded later are covered as well
document.addEventListener("click", ({ target }) => {
    const toggle = (target as HTMLElement).closest("[data-row-actions-toggle]");
    if (!toggle) {
        closeAllMenus();
        return;
    }
    const wrapper = toggle.closest("[data-row-actions]");
    const wasOpen = toggle.getAttribute("aria-expanded") === "true";
    closeAllMenus();
    if (!wasOpen) {
        openMenu(wrapper);
    }
});

document.addEventListener("keydown", ({ key }) => {
    if (key === "Escape") {
        closeAllMenus();
    }
});

// The menu does not follow its toggle button, so it is closed instead
window.addEventListener("scroll", closeAllMenus, true);
window.addEventListener("resize", closeAllMenus);
