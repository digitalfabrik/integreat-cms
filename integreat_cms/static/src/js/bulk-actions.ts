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
 *             <option>{% trans "Select bulk action" %}</option>
 *             <option data-bulk-action="{% url 'option_url' %}">{% trans "Option" %}</option>
 *             <option data-bulk-action="{% url 'option_url' %}" data-target="_blank">{% trans "Option opened in new tab" %}</option>
 *         </select>
 *
 * - Add submit button: <button id="bulk-action-execute" class="btn" disabled>{% trans "Execute" %}</button>
 *
 *  VIEW
 * ######
 *
 * Retrieve the selected page ids like this:
 *
 *     page_ids = request.POST.getlist("selected_ids[]")
 *
 */

/*
 * Update the selection count after a checkbox has been toggled
 */
const updateSelectionCount = () => {
    const selectCount = document.querySelector("[data-list-selection-count]") as HTMLElement;
    if (selectCount) {
        selectCount.innerText = document.querySelectorAll(".bulk-select-item:checked").length.toString();
    }
};

/*
 * Check whether a page does have a translation
 */
const hasTranslation = (selectItems: HTMLInputElement[]): boolean => {
    // checks if at least one of the selected pages has a translation for the current language
    const { languageSlug } = document.getElementById("pdf-export-option").dataset;
    return selectItems
        .filter((inputElement) => inputElement.checked)
        .some(
            (inputElement) => inputElement.closest("tr").querySelector(`.lang-grid .${languageSlug} .no-trans`) === null
        );
};

/*
 * Enable/disable the bulk action button
 */
export const toggleBulkActionButton = () => {
    // Only activate button if at least one item and the action is selected
    // Also check if at least one page translation exists for PDF export before activation.
    const selectItems = <HTMLInputElement[]>Array.from(document.getElementsByClassName("bulk-select-item"));
    const bulkAction = document.getElementById("bulk-action") as HTMLSelectElement;
    const bulkActionButton = document.getElementById("bulk-action-execute") as HTMLButtonElement;
    const selectedAction = bulkAction.options[bulkAction.selectedIndex];
    if (
        !selectItems.some((el) => el.checked) ||
        bulkAction.selectedIndex === 0 ||
        (selectedAction.id === "pdf-export-option" && !hasTranslation(selectItems))
    ) {
        bulkActionButton.disabled = true;
    } else {
        bulkActionButton.disabled = false;
    }
};

/*
 * Execute the selected bulk action
 */
export const bulkActionExecute = (event: Event) => {
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
};

/*
 * Check/uncheck the bulk checkboxes ot the subpages of the given page recursively
 */
const setCheckboxRecursively = (pageId: number, checked: boolean) => {
    const page = document.getElementById(`page-${pageId}`);
    const checkbox = page.querySelector(".bulk-select-item") as HTMLInputElement;
    checkbox.checked = checked;
    const toggleButton = page.querySelector(".toggle-subpages");
    if (toggleButton) {
        const childrenIds: number[] = JSON.parse(toggleButton.getAttribute("data-page-children"));
        childrenIds.forEach((childId) => setCheckboxRecursively(childId, checked));
    }
};

/**
 * Set all event handlers
 */
export const setBulkActionEventListeners = () => {
    const bulkAction = document.getElementById("bulk-action") as HTMLSelectElement;
    if (!bulkAction) {
        return;
    }
    console.debug("Set event handlers for bulk actions");
    const selectAllCheckbox = document.getElementById("bulk-select-all") as HTMLInputElement;
    const bulkActionForm = document.getElementById("bulk-action-form");
    const selectItems = <HTMLInputElement[]>Array.from(document.getElementsByClassName("bulk-select-item"));
    // Set event listener for select all checkbox
    selectAllCheckbox.classList.remove("cursor-wait");
    selectAllCheckbox.addEventListener("click", () => {
        // Set all checkboxes to the same value as the "select all" checkbox
        selectItems.forEach((checkbox) => {
            /* eslint-disable-next-line no-param-reassign */
            checkbox.checked = selectAllCheckbox.checked;
        });
        updateSelectionCount();
        toggleBulkActionButton();
    });
    // Set all checkboxes initially in case the page tree was reloaded
    selectItems.forEach((checkbox) => {
        /* eslint-disable-next-line no-param-reassign */
        checkbox.checked = selectAllCheckbox.checked;
    });
    // Update selection counter initially
    updateSelectionCount();
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
            const pageId = selectItem.getAttribute("value");
            const collapsiblePage = document.querySelector(`.toggle-subpages[data-page-id="${pageId}"]`);
            if (collapsiblePage) {
                const childrenIds: number[] = JSON.parse(collapsiblePage.getAttribute("data-page-children"));
                childrenIds.forEach((childId) => {
                    setCheckboxRecursively(childId, selectItem.checked);
                });
            }
            updateSelectionCount();
        });
    });
};

window.addEventListener("load", () => {
    // On the page tree, the event listeners are set after all subpages have been loaded
    if (!document.querySelector("[data-delay-event-handlers]")) {
        setBulkActionEventListeners();
    }
});
