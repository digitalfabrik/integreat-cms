/**
 * The functionality to fetch subpages
 */

import feather from "feather-icons";

import { setBulkActionEventListeners } from "../bulk-actions";
import { setToggleSubpagesEventListeners } from "./toggle-subpages";
import { addDragAndDropListeners } from "../tree-drag-and-drop";
import { addConfirmationDialogListeners } from "../confirmation-popups";
import { addPreviewWindowListeners, openPreviewWindowInPageTree } from "./page-preview";

window.addEventListener("load", () => {
  // Load subpages initially
  if (document.querySelector("[data-delay-event-handlers]")) {
    let rootPages: HTMLElement[] = Array.from(document.querySelectorAll(".toggle-subpages"));
    console.debug("Loading all subpages");
    Promise.all(rootPages.map(fetchSubpages)).then(() => {
      console.debug("Finished loading all subpages");
      // Render icons for recently added DOM elements
      feather.replace({ class: 'inline-block' });
      // Set event handlers
      setToggleSubpagesEventListeners();
      setBulkActionEventListeners();
      addDragAndDropListeners();
      addConfirmationDialogListeners();
      addPreviewWindowListeners(openPreviewWindowInPageTree);
    })
  }
});

/**
 * Ajax call to fetch children of selected page
 * and insert them into DOM at right position
 *
 * @param collapseSpan The page to expand its children
 */
export async function fetchSubpages(collapseSpan: HTMLElement): Promise<number[]> {
  // Get descendants of page
  let response = await fetch(collapseSpan.dataset.pageDescendantsUrl);
  if (!response.ok) {
    throw new Error("Failed with status code: " + response.status);
  }
  let html = await response.text();
  // Convert the HTML string into a document object
  let parser = new DOMParser();
  let renderedDescendants = parser.parseFromString(html, 'text/html').querySelectorAll("tr");
  if (renderedDescendants.length === 0) {
    console.debug(`All subpages of page ${collapseSpan.dataset.pageId} are archived.`);
    // Hide expanding button
    collapseSpan.classList.add("hidden");
    return;
  }
  let parentRow = collapseSpan.closest("tr");
  let currentRow = parentRow
  let directChildrenIds: number[] = [];
  let descendantIds: number[] = [];
  renderedDescendants.forEach(function(rowToInsert: HTMLTableRowElement) {
    if (rowToInsert.classList.contains("page-row")) {
      // Record children ids to update all ancestors descendants data attribute
      let descendantId = parseInt(rowToInsert.dataset.dropId);
      descendantIds.push(descendantId);
      // Check if the descendant is a direct child
      if (rowToInsert.classList.contains("level-2")) {
        directChildrenIds.push(descendantId);
      }
    }
    // Insert child into DOM tree
    currentRow.after(rowToInsert);
    // Update point to insert next child
    currentRow = rowToInsert;
  });
  // Update descendants to enable drag & drop functionality
  let dragSpan = parentRow.querySelector(".drag") as HTMLElement;
  const descendants = JSON.parse(
      dragSpan.dataset.nodeDescendants
  ) as number[];
  dragSpan.dataset.nodeDescendants = `[${descendants.concat(descendantIds)}]`;
  // Set direct children to enable expand/collapse functionality
  collapseSpan.dataset.pageChildren = `[${directChildrenIds}]`;
}
