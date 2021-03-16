window.addEventListener("load", () => {
  document.querySelectorAll(".collapsible").forEach((node) => {
    node.addEventListener("click", toggleDashboardSection);
  });

  /**
   * Handles toggling boxes on the dashboard
   * @param {Event} event Click event for dashboard containers
   */
  function toggleDashboardSection(event: Event) {
    // The button which was clicked
    const target = event.target as HTMLElement;
    const button = target.closest(".collapsible");
    // The div which should be collapsed or expanded
    const content = button.parentNode.querySelector(".collapsible-content");
    // Toggle content div
    content.classList.toggle("active");
    // Toggle arrows
    if (content.classList.contains("active")) {
      button.querySelector(".up-arrow").classList.remove("hidden");
      button.querySelector(".down-arrow").classList.add("hidden");
    } else {
      button.querySelector(".up-arrow").classList.add("hidden");
      button.querySelector(".down-arrow").classList.remove("hidden");
    }
  }
});
