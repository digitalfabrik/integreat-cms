/**
 * This file contains all functions which are needed for the bulk actions.
 *
 * Usage:
 *
 *  TEMPLATE
 * ##########
 *
 * - Add <form> around list/table
 * - Add <input type="checkbox" id="bulk-select-all"> in table head
 * - Add <input type="checkbox" name="selected_ids[]" value="{{ item.id }}" class="bulk-select-item"> in each table row
 * - Add options for all bulk actions
 *
 *         <select id="bulk-action">
 *             <option>{% trans 'Select bulk action' %}</option>
 *             <option data-bulk-action="{% url 'option_url' %}">{% trans 'Option' %}</option>
 *             <option data-bulk-action="{% url 'option_url' %}" data-target="_blank">{% trans 'Option opened in new tab' %}</option>
 *         </select>
 *
 * - Add submit button: <button id="bulk-action-execute" class="btn" disabled>{% trans 'Execute' %}</button>
 *
 *  VIEW
 * ######
 *
 * Retrieve the selected page ids like this:
 *
 *     page_ids = request.POST.getlist("selected_ids[]")
 *
 */

function isInputElement(el: Element): el is HTMLInputElement {
  return el instanceof HTMLInputElement;
}

window.addEventListener("load", () => {
  const selectAllCheckbox = document.getElementById("bulk-select-all");
  const bulkAction = document.getElementById("bulk-action") as HTMLSelectElement;
  const bulkActionForm = document.getElementById("bulk-action-form");
  const selectItems = Array.from(document.getElementsByClassName("bulk-select-item"));
  const bulkActionButton = document.getElementById(
    "bulk-action-execute"
  ) as HTMLButtonElement;

  if (selectAllCheckbox && isInputElement(selectAllCheckbox)) {
    selectAllCheckbox.addEventListener("click", () => {
      const value = selectAllCheckbox.checked;
      selectItems
        .filter(isInputElement)
        .forEach((checkbox) => (checkbox.checked = value));
      toggleBulkActionButton();
    });
  }

  if (bulkAction) {
    bulkAction.addEventListener("change", toggleBulkActionButton);
    toggleBulkActionButton();
  }
  if (bulkActionForm) {
    bulkActionForm.addEventListener("submit", bulkActionExecute);
  }

  selectItems.forEach((el) => {
    el.addEventListener("change", toggleBulkActionButton);
  });

  function toggleBulkActionButton() {
    // Only activate button if at least one item and the action is selected
    // also check if at least one page translation exists for PDF export before activation
    let selectedAction = bulkAction.options[bulkAction.selectedIndex];
    if (
      !selectItems
        .filter(isInputElement)
        .some((el) => el.checked) ||
      bulkAction.selectedIndex === 0 ||
      (selectedAction.id === "pdf-export-option" && !hasTranslation())
    ) {
      bulkActionButton.disabled = true;
    } else {
      bulkActionButton.disabled = false;
    }
  }

  function bulkActionExecute(event: Event) {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const selectedAction = bulkAction.options[bulkAction.selectedIndex];
    // Set form action to url of the bulk action
    form.action = selectedAction.getAttribute("data-bulk-action");
    // Set form target in case action is to be opened in a new tab
    const target = selectedAction.getAttribute("data-target");
    if (target !== null) {
      form.target = target;
    }
    // Submit form and execute bulk action
    form.submit();
  }

  function hasTranslation(): boolean {
    // checks if at least one of the selected pages has a translation for the current language
    let languageSlug = document.getElementById("pdf-export-option").dataset.languageSlug;
    return selectItems
      .filter(isInputElement)
      .filter(inputElement => inputElement.checked)
      .some(inputElement => {
        return inputElement
          .closest("tr")
          .querySelector(`.lang-grid .${languageSlug} .no-trans`) === null;
      });
  }
});
