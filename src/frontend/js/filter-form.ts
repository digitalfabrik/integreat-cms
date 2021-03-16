/*
 * Scripts for filter forms
 */
window.addEventListener("load", () => {
  // event handler to toggle filter form
  const toggleButton = document.getElementById("filter-toggle");
  if (toggleButton) {
    toggleButton.addEventListener("click", () => {
      document
        .getElementById("filter-form-container")
        .classList.toggle("hidden");
      document
        .querySelectorAll("filter-toggle-text")
        .forEach((element) => element.classList.toggle("hidden"));
    });
  }

  // event handler to reset filter form
  const resetFilterButton = document.getElementById("filter-reset");
  if (resetFilterButton) {
    resetFilterButton.addEventListener("click", ({ target }) => {
      const form = (target as HTMLElement).closest("form");
      [
        ...form.querySelectorAll("input"),
        ...form.getElementsByTagName("select"),
      ].forEach((node) => resetToDefaultValue(node));
    });
  }
});

function resetToDefaultValue(node: HTMLSelectElement | HTMLInputElement) {
  if (
    node instanceof HTMLInputElement &&
    node.getAttribute("type") === "checkbox"
  ) {
    if (node.classList.contains("default-checked")) {
      // Checkbox marked to be checked by default
      node.checked = true;
    } else if (node.classList.contains("default-not-checked")) {
      // Checkbox marked to be unchecked by default
      node.checked = false;
    }
  } else if (node.classList.contains("default-value")) {
    // Non-checkbox input marked to have a default value
    node.value = node.getAttribute("data-default-value");
  }
}
