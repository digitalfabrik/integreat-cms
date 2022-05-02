/**
 * This file contains a function to count and update the number of selected items in the page tree.
 */

export function addCheckboxCountListeners() {
  document.querySelectorAll(".bulk-select-item").forEach((el) =>
    el.addEventListener("change", () => {
      (document.querySelector("[data-list-selection-count]") as HTMLElement).innerText =
        document.querySelectorAll(".bulk-select-item:checked").length.toString();
    })
  );
}
