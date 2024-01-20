/**
 * The functionality to fetch subpages
 */

import { createIconsAt } from "../utils/create-icons";
import { getCsrfToken } from "../utils/csrf-token";
import { setBulkActionEventListeners } from "../bulk-actions";
import { setToggleSubpagesEventListeners } from "./toggle-subpages";
import { addDragAndDropListeners } from "../tree-drag-and-drop";
import { addConfirmationDialogListeners } from "../confirmation-popups";
import { addPreviewWindowListeners, openPreviewWindowInPageTree } from "./page-preview";
import { restorePageTreeLayout } from "./persistent_page_tree";

/**
 * Function to insert children of selected page into DOM at right position
 *
 * @param collapseSpan The page to expand its children
 */
const fetchSubpages = (collapseSpan: HTMLElement, html: string) => {
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
            console.log(rowToInsert.classList);
            if (rowToInsert.classList.contains("level-2")) {
                directChildrenIds.push(descendantId);
            }
        }
        // render icons
        console.log(rowToInsert);
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

const fetchAllSubpages = async (url: string, pages: HTMLElement[]) => {
    const ids = pages.map((page) => page.dataset.pageId);
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(ids),
    });

    const nodes = (await response.json()).data;

    for (let i = 0; i < pages.length; i += 1) {
        fetchSubpages(pages[i], nodes[i]);
    }
};

window.addEventListener("load", async () => {
    // Load subpages initially
    const table: HTMLElement = document.querySelector("[data-delay-event-handlers]");
    if (table) {
        const rootPages: HTMLElement[] = Array.from(document.querySelectorAll(".toggle-subpages"));
        const url = table.dataset.descendantsUrl;
        console.debug("Loading all subpages");

        const expandedRows: Set<number> = new Set(JSON.parse(window.sessionStorage.getItem("page_state")));
        const openPages = rootPages.filter((page) => expandedRows.has(Number(page.dataset.pageId)));
        const closedPages = rootPages.filter((page) => !expandedRows.has(Number(page.dataset.pageId)));

        await fetchAllSubpages(url, openPages);
        restorePageTreeLayout();

        await fetchAllSubpages(url, closedPages);

        console.debug("Finished loading all subpages");
        // Set event handlers
        setToggleSubpagesEventListeners();
        setBulkActionEventListeners();
        addDragAndDropListeners();
        addConfirmationDialogListeners();
        addPreviewWindowListeners(openPreviewWindowInPageTree);
    }
});
