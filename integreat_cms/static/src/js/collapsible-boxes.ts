window.addEventListener("load", () => {
    document.querySelectorAll(".collapsible").forEach((node) => {
        node.addEventListener("click", toggleDashboardSection);
    });
});

/**
 * Handles toggling boxes on the dashboard
 * @param {Event} event Click event for dashboard containers
 */
async function toggleDashboardSection({ target }: Event): Promise<void> {
    // Toggle arrows of the clicked widget
    const collapsible = (target as HTMLElement).closest(".collapsible");
    collapsible.querySelector(".up-arrow").classList.toggle("hidden");
    collapsible.querySelector(".down-arrow").classList.toggle("hidden");
    // Toggle the content div which should be collapsed or expanded
    const content = collapsible.parentNode.querySelector(".collapsible-content") as HTMLElement;
    // Check if content is currently collapsed or not
    if (content.clientHeight === 0) {
        // Temporarily set height to auto to allow to grow to its total potential height
        content.style.height = "auto";
        // Get the actual height
        let potentialHeight = content.clientHeight + "px";
        // Immediately reset to zero
        content.style.height = "0px";
        // Set the height to a fixed numerical value with a timeout for the transition
        setTimeout(() => (content.style.height = potentialHeight));
        // After the potential height is restored, change this value to "auto" to not break things when window is resized
        setTimeout(() => (content.style.height = "auto"), 200);
    } else {
        // Set height to explicit numerical value instead of "auto" to enable continuous transition
        content.style.height = content.clientHeight + "px";
        // Use timeout to allow a smooth transition
        setTimeout(() => (content.style.height = "0px"));
    }
}
