/**
 * This file contains functions for persisting and restoring the expanded state of the page tree.
 */

import { toggleSubpagesForElement } from "./toggle-subpages";

/**
 * This function restores the state of the page tree.
 * Rows that are not visible won't get expanded.
 */
export const restorePageTreeLayout = () => {
    let collapsedRows: number[] = JSON.parse(window.sessionStorage.getItem("page_state"));
    if (!collapsedRows) {
        return;
    }

    const allSpans = Array.from(document.querySelectorAll(".toggle-subpages"));

    // Try expanding rows until no new visible rows can get expanded.
    // This approach is used because pages that are not visible should not get expanded,
    // and expanding a page can make its children visible.
    while (collapsedRows.length > 0) {
        const stillCollapsedRows = collapsedRows.filter((row) => {
            const span = allSpans.find((span) => JSON.parse(span.getAttribute("data-page-id")) === row);
            if (span && !span.closest("tr").classList.contains("hidden")) {
                toggleSubpagesForElement(span as HTMLSpanElement);
                return false;
            }
            return true;
        });

        if (collapsedRows.length === stillCollapsedRows.length) {
            break;
        }

        collapsedRows = stillCollapsedRows;
    }
};

/**
 * This function updates the expanded state of the given page row.
 * This state is stored in the session storage.
 *
 * @param pageId The id of the page to update
 * @param expanded Whether the page is now expanded or collapsed
 */
export const storeExpandedState = (pageId: number, expanded: boolean) => {
    const expandedRows = new Set(JSON.parse(window.sessionStorage.getItem("page_state")) || []);
    if (expanded) {
        expandedRows.add(pageId);
    } else {
        expandedRows.delete(pageId);
    }
    // The key can be independent of a region id, because different urls have different sessionStorage
    window.sessionStorage.setItem("page_state", JSON.stringify(Array.from(expandedRows)));
};
