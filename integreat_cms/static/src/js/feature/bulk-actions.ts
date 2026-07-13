/**
 * Handles bulk actions on list views — selecting items, enabling the execute button, and submitting the action form.
 *
 * Attached to the root element via `data-js-bulk-actions`.
 * Expects the following elements within root:
 *   - `#bulk-action-form`           — the form to submit (omit if root itself is the form)
 *   - `#bulk-select-all`            — checkbox to select/deselect all items
 *   - `.bulk-select-item`           — per-row checkboxes (may be added dynamically via AJAX)
 *   - `#bulk-action`                — select element listing available bulk actions
 *   - `#bulk-action-execute`        — submit button, enabled only when items and an action are selected
 *   - `[data-list-selection-count]` — element displaying the number of selected items
 *
 * Each `<option>` in `#bulk-action` may carry:
 *   - `data-bulk-action`       — URL to set as the form action on submit
 *   - `data-target`            — optional form target (e.g. `_blank` for PDF export in a new tab)
 *   - `.bulk-confirmation-dialog` + `data-popup-title`, `data-popup-subject`, `data-popup-text`
 *                              — show a confirmation dialog before submitting
 *
 * Uses event delegation on the root for `.bulk-select-item` changes so dynamically
 * inserted rows (e.g. from async page tree loading) are handled without re-initialisation.
 *
 * @module bulk-actions
 */

import { defineFeature } from "../utils/define-feature";
import { showConfirmationPopupWithData } from "../utils/confirmation-popup";

const updateSelectionCount = (root: HTMLElement) => {
    const selectCount = root.querySelector("[data-list-selection-count]") as HTMLElement;
    if (selectCount) {
        selectCount.innerText = root.querySelectorAll(".bulk-select-item:checked").length.toString();
    }
};

const hasTranslation = (root: HTMLElement, selectItems: HTMLInputElement[]): boolean => {
    // At least one selected page must have a translation for the current language to enable PDF export
    const { languageSlug } = (root.querySelector("#pdf-export-option") as HTMLElement).dataset;
    return selectItems
        .filter((el) => el.checked)
        .some((el) => el.closest("tr")?.querySelector(`.lang-grid .${languageSlug} .no-trans`) === null);
};

const toggleBulkActionButton = (root: HTMLElement) => {
    const selectItems = Array.from(root.querySelectorAll<HTMLInputElement>(".bulk-select-item"));
    const bulkAction = root.querySelector<HTMLSelectElement>("#bulk-action");
    const bulkActionButton = root.querySelector<HTMLButtonElement>("#bulk-action-execute");
    const selectedAction = bulkAction.options[bulkAction.selectedIndex];
    bulkActionButton.disabled =
        !selectItems.some((el) => el.checked) ||
        bulkAction.selectedIndex === 0 ||
        // For PDF export, also require at least one selected page to have a translation
        (selectedAction.id === "pdf-export-option" && !hasTranslation(root, selectItems));
};

const bulkActionExecute = (event: Event, root: HTMLElement) => {
    event.preventDefault();
    const bulkAction = root.querySelector<HTMLSelectElement>("#bulk-action");
    const form = root instanceof HTMLFormElement ? root : root.querySelector<HTMLFormElement>("#bulk-action-form");
    if (!form) {
        return;
    }
    const initialTarget = form.target;
    const selectedAction = bulkAction.options[bulkAction.selectedIndex];
    const action = selectedAction.getAttribute("data-bulk-action");
    if (action) {
        const url = new URL(action, window.location.origin);
        if (url.origin === window.location.origin) {
            form.action = url.pathname + url.search; // lgtm[js/xss-through-dom]
        }
    }
    const target = selectedAction.getAttribute("data-target");
    if (target !== null) {
        form.target = target;
    }
    if (selectedAction.classList.contains("bulk-confirmation-dialog")) {
        showConfirmationPopupWithData(
            selectedAction.getAttribute("data-popup-subject"),
            selectedAction.getAttribute("data-popup-title"),
            selectedAction.getAttribute("data-popup-text"),
            () => form.submit()
        );
    } else {
        form.submit();
    }
    // Reset target so subsequent actions (e.g. after a PDF export) don't inadvertently open in a new tab
    form.target = initialTarget;
};

const setCheckboxRecursively = (root: HTMLElement, pageId: number, checked: boolean) => {
    const page = root.querySelector(`#page-${pageId}`);
    const checkbox = page.querySelector(".bulk-select-item") as HTMLInputElement;
    checkbox.checked = checked;
    const toggleButton = page.querySelector(".toggle-subpages");
    if (toggleButton) {
        const childrenIds: number[] = JSON.parse(toggleButton.getAttribute("data-page-children"));
        childrenIds.forEach((childId) => setCheckboxRecursively(root, childId, checked));
    }
};

export default defineFeature((root) => {
    console.debug("Set event handlers for bulk actions");

    const selectAllCheckbox = root.querySelector<HTMLInputElement>("#bulk-select-all");
    const bulkAction = root.querySelector<HTMLSelectElement>("#bulk-action");
    const form = root instanceof HTMLFormElement ? root : root.querySelector<HTMLFormElement>("#bulk-action-form");

    if (!bulkAction || !selectAllCheckbox || !form) {
        return;
    }

    // Sync initial checkbox state in case the page tree was reloaded
    root.querySelectorAll<HTMLInputElement>(".bulk-select-item").forEach((checkbox) => {
        /* eslint-disable-next-line no-param-reassign */
        checkbox.checked = selectAllCheckbox.checked;
    });

    updateSelectionCount(root);
    bulkAction.addEventListener("change", () => toggleBulkActionButton(root));
    toggleBulkActionButton(root);
    form.addEventListener("submit", (event) => bulkActionExecute(event, root));

    selectAllCheckbox.addEventListener("click", () => {
        root.querySelectorAll<HTMLInputElement>(".bulk-select-item").forEach((checkbox) => {
            /* eslint-disable-next-line no-param-reassign */
            checkbox.checked = selectAllCheckbox.checked;
        });
        updateSelectionCount(root);
        toggleBulkActionButton(root);
    });

    // Once async subpage loading finishes, remove cursor-wait from bulk checkboxes
    document.addEventListener(
        "subpages-loaded",
        () => {
            root.querySelectorAll<HTMLElement>(".bulk-select-item.cursor-wait, #bulk-select-all.cursor-wait").forEach(
                (el) => el.classList.remove("cursor-wait")
            );
        },
        { once: true }
    );

    // Event delegation handles checkboxes added dynamically (e.g. async page tree loading)
    root.addEventListener("change", (e) => {
        const target = e.target as HTMLElement;
        if (!target.matches(".bulk-select-item")) {
            return;
        }
        const selectItem = target as HTMLInputElement;
        toggleBulkActionButton(root);
        // If the page has subpages, propagate the checked state recursively
        const pageId = selectItem.getAttribute("value");
        const collapsiblePage = root.querySelector(`.toggle-subpages[data-page-id="${pageId}"]`);
        if (collapsiblePage) {
            const childrenIds: number[] = JSON.parse(collapsiblePage.getAttribute("data-page-children"));
            childrenIds.forEach((childId) => setCheckboxRecursively(root, childId, selectItem.checked));
        }
        updateSelectionCount(root);
    });
});
