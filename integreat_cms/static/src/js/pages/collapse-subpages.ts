import feather from "feather-icons";

import { addDragAndDropListeners } from "../tree-drag-and-drop";
import { addConfirmationDialogListeners } from "../confirmation-popups";
import { toggleBulkActionButton }from "../bulk-actions";

/*
 * The functionality to toggle subpages
 */

window.addEventListener("load", () => {
  // event handler to hide and show subpages
  document
    .querySelectorAll(".collapse-subpages")
    .forEach((el) => el.addEventListener("click", toggleSubpages));
});

/**
 * This function toggles all subpages of the clicked page and changes the icon
 * 
 * @param event Collapse/Expand button clicked
 */
async function toggleSubpages(event: Event) {
  event.preventDefault();
  // Get span with all data options
  let collapseSpan = (event.target as HTMLElement).closest("span");
  const children: number[] = JSON.parse(
    collapseSpan.getAttribute("data-page-children")
  );
  if (children.length === 0) {
    // children have not been loaded yet, toggle loading spinner
    collapseSpan.querySelector("svg").classList.toggle("hidden");
    collapseSpan.querySelector(".animate-spin").classList.toggle("hidden");
    let childrenIds = await fetchSubpages(collapseSpan)
    .catch(e => {
      console.log('There has been a problem with your fetch operation: ' + e.message);
    });
    if (childrenIds && childrenIds.length === 0) {
      // page is not a leaf node but endpoint returns no children
      // => all subpages are archived, then display information message and quit
      collapseSpan.querySelector(".animate-spin").classList.toggle("hidden");
      document.querySelector("#archived-subpages-only").classList.toggle("hidden");
      return;
    }
    // add listeners for recently added DOM elements
    addDragAndDropListeners();
    addConfirmationDialogListeners();
    collapseSpan.querySelector("svg").classList.toggle("hidden");
  }
  // Toggle subpages
  toggleSubpagesRecursive(children);
  // Change icon
  let icon = collapseSpan.querySelector("svg");
  if (icon.classList.contains("feather-chevron-down")) {
    collapseSpan.innerHTML = '<i data-feather="chevron-right"></i>';
  } else {
    collapseSpan.innerHTML = '<i data-feather="chevron-down"></i>';
  }
  // Toggle title
  const titleBuffer = collapseSpan.title;
  collapseSpan.title = collapseSpan.getAttribute("data-alt-title");
  collapseSpan.setAttribute("data-alt-title", titleBuffer);
  // Trigger icon replacement
  feather.replace({ class: 'inline-block' });
}

/**
 * This function iterates over all direct children of a page and
 * toggles their "hidden" class if they are not yet collapsed.
 * This enables to "save" the collapsed-state of all subpages, so when showing the subpages again,
 * all previously collapsed subpages will remain collapsed.
 * 
 * @param children Nodes to be toggled
 */
function toggleSubpagesRecursive(childrenIds: Array<number>) {
  // Foreach child: toggle class "hidden" and proceed for all children which are not explicitly hidden themselves
  childrenIds.forEach((childId) => {
    // Get child table row
    const child = document.getElementById("page-" + childId);
    // Hide/show table row
    child.classList.toggle("hidden");
    // Remove the left sibling from possible drop targets while it is collapsed
    document
      .getElementById("page-" + childId + "-drop-left")
      ?.classList.toggle("drop-between");
    // Find out whether this page has children itself
    const collapseSpan = child.querySelector(
      ".collapse-subpages"
    ) as HTMLElement;
    if (collapseSpan) {
      // The icon will be null if the page is a leaf node
      const icon = collapseSpan.querySelector("svg");
      if (icon.classList.contains("feather-chevron-down")) {
        // This means the children are not yet collapsed and have to be hidden as well
        const grandChildren: number[] = JSON.parse(
          collapseSpan.getAttribute("data-page-children")
        );
        toggleSubpagesRecursive(grandChildren);
      }
    }
  });
}

/**
 * Ajax call to fetch children of selected page 
 * and insert them into DOM at right position
 * 
 * @param collapseSpan The page to expand its children
 * @returns Array of children ids
 */
async function fetchSubpages(collapseSpan: HTMLElement): Promise<number[]> {
  // Get children of page
  let response = await fetch(collapseSpan.dataset.pageChildrenUrl);
  if (!response.ok) {
    throw new Error("Failed with status code: " + response.status);
  }
  let html = await response.text();
  var childrenIds: number[] = [];
  // Convert the HTML string into a document object
	let parser = new DOMParser();
	let childrenDoc = parser.parseFromString(html, 'text/html');
  if (childrenDoc.querySelectorAll("tr").length === 0) {
    return childrenIds;
  }
  let parentRow = collapseSpan.closest("tr");
  childrenDoc.querySelectorAll("tr").forEach(function(rowToinsert: HTMLTableRowElement) {
    let newCollapseSpan = rowToinsert.querySelector(".collapse-subpages");
    let newCheckbox = rowToinsert.querySelector(".bulk-select-item");
    if (newCollapseSpan) {
      // add event listener for page expansion if not leaf node
      newCollapseSpan.addEventListener("click", toggleSubpages);
    }
    if (newCheckbox) {
      // add event listener to update bulk action button
      newCheckbox.addEventListener("change", toggleBulkActionButton);
    }
    if (!rowToinsert.classList.contains("drop-between")) {
      // record children ids to update all ancestors descendants data attribute
      childrenIds.push(parseInt(rowToinsert.dataset.dropId));
    }
    // insert child into DOM tree
    parentRow.parentNode.insertBefore(rowToinsert, parentRow.nextSibling);
    // update point to insert next child
    parentRow = rowToinsert;
  });
  updateDescendants(childrenDoc, childrenIds);
  updateChildren(collapseSpan, childrenIds);
  // render icons for recently added DOM elements
  feather.replace({ class: 'inline-block' });
  return childrenIds;
}

/**
 * Adds new descendants to data-node-descendants of all ancestor
 * 
 * @param childrenDoc document containing ancestor information
 * @param childrenIds the chidlren ids to be added
 */
function updateDescendants(childrenDoc: Document, childrenIds: Array<number>) {
  // get ids of all ancestors for the selected page
  let ancestors = JSON.parse(
    (<HTMLElement>childrenDoc.querySelector("#ancestors")).dataset.ancestors
  ) as number[];
  ancestors.forEach(function(ancestor: number) {
    // as new children were added to the DOM, all ancestors have to update their descendants 
    let ancestorDragSpan = <HTMLElement>document.querySelector("#page-" + ancestor + " .drag");
    const descendants = JSON.parse(
      ancestorDragSpan.dataset.nodeDescendants
    ) as number[];
    // update descendants
    ancestorDragSpan.dataset.nodeDescendants = `[${descendants.concat(childrenIds)}]`;
  })
}

/**
 * Add recently fetched children ids to collapse span dataset
 * 
 * @param collapseSpan parent element to be updated
 * @param childrenIds ids to be appended
 */
function updateChildren(collapseSpan: HTMLElement, childrenIds: Array<number>) {
  const currentChidlrenIds = JSON.parse(
    collapseSpan.dataset.pageChildren
  ) as number[];
  collapseSpan.dataset.pageChildren = `[${currentChidlrenIds.concat(childrenIds)}]`;
}

