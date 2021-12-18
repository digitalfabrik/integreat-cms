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
      Array.from(document.getElementsByClassName("filter-toggle-text"))
        .forEach((element) => element.classList.toggle("hidden"));
    });
  }

  // event handler to reset filter form
  const resetFilterButton = document.getElementById("filter-reset");
  if (resetFilterButton) {
    resetFilterButton.addEventListener("click", ({ target }) => {
      const form = (target as HTMLElement).closest("form");
      for (let node of form.elements) {
        if (node.matches("input") || node.matches("select")) {
          resetToDefaultValue(node as HTMLInputElement | HTMLSelectElement);
        }
      }
    });
  }

  // event handler to specify custom default-checked or default-not-checked attributes
  document.querySelectorAll("input[data-default-checked-value]").forEach(node => {
    const checkbox = node as HTMLInputElement;
    if (checkbox.value == checkbox.getAttribute("data-default-checked-value")) {
      checkbox.classList.add("default-checked");
    } else {
      checkbox.classList.add("default-not-checked");
    }
  });
});

function resetToDefaultValue(node: HTMLSelectElement | HTMLInputElement) {
  if (
    node instanceof HTMLInputElement &&
    node.getAttribute("type") === "checkbox"
  ) {
    if (node.classList.contains("default-checked") && !node.checked) {
      // Checkbox marked to be checked by default
      node.click();
    } else if (node.classList.contains("default-not-checked") && node.checked) {
      // Checkbox marked to be unchecked by default
      node.click();
    }
  } else if (node.classList.contains("default-value")) {
    // Non-checkbox input marked to have a default value
    node.value = node.getAttribute("data-default-value");
  }
}
