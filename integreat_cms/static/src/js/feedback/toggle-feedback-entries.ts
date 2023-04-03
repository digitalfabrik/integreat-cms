/*
 * This file provides a simple spoiler for feedback list entries with hide/show functionality.
 */
window.addEventListener("icon-load", () => {
    // Check which feedback entries need the toggle button
    document.querySelectorAll(".table-cell-content").forEach((element) => {
        if ((element as HTMLElement).offsetWidth >= element.scrollWidth) {
            // Remove toggle button if not necessary
            element.parentElement.querySelector(".toggle-table-cell").remove();
        }
    });
    // Set event handlers for expanding/collapsing feedback entries
    document.querySelectorAll(".toggle-table-cell").forEach((toggle) => {
        toggle.addEventListener("click", (_) => {
            toggle.parentElement.classList.toggle("active");
        });
    });
});
