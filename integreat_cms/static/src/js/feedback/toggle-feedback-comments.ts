/*
 * This file provides a simple spoiler for feedback comments with hide/show functionality.
 */
window.addEventListener("icon-load", () => {
  // Check which feedback entries need the toggle button
  document.querySelectorAll(".feedback-comment-preview").forEach((element) => {
    if ((element as HTMLElement).offsetWidth >= element.scrollWidth) {
      // Remove toggle button if not necessary
      (element.parentNode as HTMLElement).querySelector(".toggle-feedback-comment").remove();
    }
  });
  // Set event handlers for expanding/collapsing feedback comments
  document.querySelectorAll(".toggle-feedback-comment").forEach((toggle) =>
    toggle.addEventListener("click", ({ target }) => {
      [...(target as HTMLElement).closest(".feedback-comment").children].forEach((node) => {
        (node as HTMLElement).classList.toggle("hidden");
      });
    })
  );
});
