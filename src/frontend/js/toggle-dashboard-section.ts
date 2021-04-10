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
  const content = collapsible.parentNode.querySelector(".collapsible-content");
  content.classList.toggle("max-h-160");
  content.classList.toggle("max-h-0");
}
