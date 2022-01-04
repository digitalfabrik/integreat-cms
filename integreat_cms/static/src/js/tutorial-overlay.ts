document.addEventListener("DOMContentLoaded", () => {
  /* Hide the overlay when the form is submitted, mark a tutorial as dismissed if the checkbox was set */
  document
    .querySelectorAll("form[data-tutorial-overlay-form]")
    .forEach((overlayForm) => {
      overlayForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const data = new FormData(overlayForm as HTMLFormElement);
        if (data.get("dismiss_tutorial")) {
          fetch(overlayForm.getAttribute("action"), {
            method: overlayForm.getAttribute("method"),
            body: data,
          });
        }
        const overlayHost = overlayForm.closest("[data-tutorial-overlay]");
        if (overlayHost) {
          overlayHost.classList.add("hidden");
          overlayHost.classList.remove("flex");
        }
      });
    });

  /* Hide the overlay when the backdrop is clicked */
  document
    .querySelectorAll("[data-tutorial-overlay]")
    .forEach((overlayHost) => {
      overlayHost.addEventListener("click", (e) => {
        if (e.target === overlayHost) {
          overlayHost.classList.add("hidden");
          overlayHost.classList.remove("flex");
        }
      });
    });

  /* Allow to place buttons to show certain tutorials again */
  document.querySelectorAll("[data-show-tutorial]").forEach((showButton) => {
    const tutorialId = showButton.getAttribute("data-show-tutorial");
    const overlayHost = document.querySelector(
      `[data-tutorial-overlay="${tutorialId}"]`
    );
    if (!overlayHost) {
      return;
    }
    showButton.addEventListener("click", () => {
      overlayHost.classList.remove("hidden");
      overlayHost.classList.add("flex");
    });
  });
});
