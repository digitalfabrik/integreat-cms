/**
 * This file contains all functions which are needed for the bulk actions.
 *
 * Usage:
 *
 *  TEMPLATE
 * ##########
 *
 * - Add <form id="bulk-action-form" method="post"> around list/table
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

 import { addCheckboxCountListeners } from "./checkbox-count"


window.addEventListener("load", () => {
  // On the page tree, the event listeners are set after all subpages have been loaded
  if (!document.querySelector("[data-delay-event-handlers]")) {
    setBulkActionEventListeners();
  }
});

/**
 * Set all event handlers
 */
export function setBulkActionEventListeners(){
  const bulkAction = document.getElementById("bulk-action") as HTMLSelectElement;
  if (!bulkAction) return;
  console.debug("Set event handlers for bulk actions");
  const selectAllCheckbox = document.getElementById("bulk-select-all") as HTMLInputElement;
  const bulkActionForm = document.getElementById("bulk-action-form");
  const selectItems = <HTMLInputElement[]>Array.from(document.getElementsByClassName("bulk-select-item"));
  // Set event listener for select all checkbox
  selectAllCheckbox.classList.remove("cursor-wait");
  selectAllCheckbox.addEventListener("click", () => {
    // Set all checkboxes to the same value as the "select all" checkbox
    selectItems.forEach((checkbox) => setCheckboxChecked(checkbox, selectAllCheckbox.checked)); 
    toggleBulkActionButton();
  });
  // Set all checkboxes initially in case the page tree was reloaded
  selectItems.forEach((checkbox) => setCheckboxChecked(checkbox, selectAllCheckbox.checked));
  // Set event listener for bulk action button
  bulkAction.addEventListener("change", toggleBulkActionButton);
  toggleBulkActionButton();
  // Set event listener for bulk action form
  bulkActionForm.addEventListener("submit", bulkActionExecute);
  // Set event listener for bulk action checkboxes
  selectItems.forEach((selectItem) => {
    selectItem.classList.remove("cursor-wait");
    selectItem.addEventListener("change", () => {
      toggleBulkActionButton();
      // Check if checkbox belongs to a page with subpages
      let pageId = selectItem.getAttribute("value");
      let collapsiblePage = document.querySelector(`.toggle-subpages[data-page-id="${pageId}"]`)
      if (collapsiblePage) {
        let childrenIds : number[] = JSON.parse(collapsiblePage.getAttribute("data-page-children"));
        childrenIds.forEach(childId => {
          setCheckboxRecursively(childId, selectItem.checked);
        });
      }
    });
  });
  // Activate Selection Count for events, feedback and pois
  addCheckboxCountListeners();
}

/*
 * Check/uncheck the bulk checkboxes ot the subpages of the given page recursively
 */
function setCheckboxRecursively(pageId: number, checked: boolean) {
  let page = document.getElementById("page-" + pageId);
  let checkbox = page.querySelector(".bulk-select-item") as HTMLInputElement;
  setCheckboxChecked(checkbox, checked);
  const toggleButton = page.querySelector(".toggle-subpages")
  if (toggleButton){
    let childrenIds: number[] = JSON.parse(toggleButton.getAttribute("data-page-children"));
    childrenIds.forEach((childId) => setCheckboxRecursively(childId, checked));
  }
}

/*
 * Execute the selected bulk action
 */
function bulkActionExecute(event: Event) {
  event.preventDefault();
  const bulkAction = document.getElementById("bulk-action") as HTMLSelectElement;
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

/*
 * Enable/disable the bulk action button
 */
export function toggleBulkActionButton() {
  // Only activate button if at least one item and the action is selected
  // also check if at least one page translation exists for PDF export before activation
  const selectItems = <HTMLInputElement[]>Array.from(document.getElementsByClassName("bulk-select-item"));
  const bulkAction = document.getElementById("bulk-action") as HTMLSelectElement;
  const bulkActionButton = document.getElementById(
    "bulk-action-execute"
  ) as HTMLButtonElement;
  let selectedAction = bulkAction.options[bulkAction.selectedIndex];
  if (
    !selectItems
      .some((el) => el.checked) ||
    bulkAction.selectedIndex === 0 ||
    (selectedAction.id === "pdf-export-option" && !hasTranslation(selectItems))
  ) {
    bulkActionButton.disabled = true;
  } else {
    bulkActionButton.disabled = false;
  }
}

/*
 * Check whether a page does have a translation
 */
function hasTranslation(selectItems: HTMLInputElement[]): boolean {
  // checks if at least one of the selected pages has a translation for the current language
  let languageSlug = document.getElementById("pdf-export-option").dataset.languageSlug;
  return selectItems
    .filter(inputElement => inputElement.checked)
    .some(inputElement => {
      return inputElement
        .closest("tr")
        .querySelector(`.lang-grid .${languageSlug} .no-trans`) === null;
    });
}

/*
 * Trigger a custom event for correct calculation of the change triggers.
 */
function setCheckboxChecked(checkbox: HTMLInputElement, checked: boolean) {
  checkbox.checked = checked;
  checkbox.dispatchEvent(new InputEvent("change"));
} 