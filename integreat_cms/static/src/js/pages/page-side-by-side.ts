/**
 * This file contains all functions which are needed for the page side by side view dropdown and button.
 */

const toggleSbsButton = ({ target }: Event) => {
    const linkTarget = (target as HTMLInputElement).value;
    const sideBySideLink = document.getElementById("side-by-side-link") as HTMLLinkElement;
    if (linkTarget !== "") {
        sideBySideLink.setAttribute("href", encodeURI(linkTarget));
        sideBySideLink.removeAttribute("disabled");
    } else {
        sideBySideLink.removeAttribute("href");
        sideBySideLink.setAttribute("disabled", "disabled");
    }
};
document.addEventListener("DOMContentLoaded", () => {
    const sideBySideSelect = document.getElementById("side-by-side-select") as HTMLSelectElement;
    sideBySideSelect?.addEventListener("change", toggleSbsButton);
    sideBySideSelect?.dispatchEvent(new Event("change"));
});
