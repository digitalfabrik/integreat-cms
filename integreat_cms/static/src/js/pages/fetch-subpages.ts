/**
 * The functionality to fetch subpages
 */

import { createIconsAt } from "../utils/create-icons";
import { setBulkActionEventListeners } from "../bulk-actions";
import { setToggleSubpagesEventListeners } from "./toggle-subpages";
import { addDragAndDropListeners } from "../tree-drag-and-drop";
import { addConfirmationDialogListeners } from "../confirmation-popups";
import { addPreviewWindowListeners, openPreviewWindowInPageTree } from "./page-preview";
import { restorePageLayout } from "./persistent_page_tree";

/**
 * Ajax call to fetch children of selected page
 * and insert them into DOM at right position
 *
 * @param collapseSpan The page to expand its children
 */
export const fetchSubpages = async (collapseSpan: HTMLElement): Promise<number[]> => {
    // Get descendants of page
    const response = await fetch(collapseSpan.dataset.pageDescendantsUrl);
    if (!response.ok) {
        throw new Error(`Failed with status code: ${response.status}`);
    }
    const html = await response.text();
    // Convert the HTML string into a document object
    const parser = new DOMParser();
    const renderedDescendants = parser.parseFromString(html, "text/html").querySelectorAll("tr");
    if (renderedDescendants.length === 0) {
        console.debug(`All subpages of page ${collapseSpan.dataset.pageId} are archived.`);
        // Hide expanding button
        collapseSpan.classList.add("hidden");
        return;
    }
    const parentRow = collapseSpan.closest("tr");
    let currentRow = parentRow;
    const directChildrenIds: number[] = [];
    const descendantIds: number[] = [];
    renderedDescendants.forEach((rowToInsert: HTMLTableRowElement) => {
        if (rowToInsert.classList.contains("page-row")) {
            // Record children ids to update all ancestors descendants data attribute
            const descendantId = parseInt(rowToInsert.dataset.dropId, 10);
            descendantIds.push(descendantId);
            // Check if the descendant is a direct child
            if (rowToInsert.classList.contains("level-2")) {
                directChildrenIds.push(descendantId);
            }
        }
        // render icons
        createIconsAt(rowToInsert);
        // Insert child into DOM tree
        currentRow.after(rowToInsert);
        // Update point to insert next child
        currentRow = rowToInsert;
    });
    // Update descendants to enable drag & drop functionality
    const dragSpan = parentRow.querySelector(".drag") as HTMLElement;
    const descendants = JSON.parse(dragSpan.dataset.nodeDescendants) as number[];
    dragSpan.dataset.nodeDescendants = `[${descendants.concat(descendantIds)}]`;
    // Set direct children to enable expand/collapse functionality
    /* eslint-disable-next-line no-param-reassign */
    collapseSpan.dataset.pageChildren = `[${directChildrenIds}]`;
};

window.addEventListener("load", () => {
    // Load subpages initially
    if (document.querySelector("[data-delay-event-handlers]")) {
        const rootPages: HTMLElement[] = Array.from(document.querySelectorAll(".toggle-subpages"));
        console.debug("Loading all subpages");
        Promise.all(rootPages.map(fetchSubpages)).then(() => {
            console.debug("Finished loading all subpages");
            // Set event handlers
            setToggleSubpagesEventListeners();
            setBulkActionEventListeners();
            addDragAndDropListeners();
            addConfirmationDialogListeners();
            addPreviewWindowListeners(openPreviewWindowInPageTree);
        });
    }
});
