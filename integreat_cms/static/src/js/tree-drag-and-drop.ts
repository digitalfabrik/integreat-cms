/**
 * This file contains all event handlers and functions which are needed for drag & drop functionality in trees.
 * Currently, this is used in integreat_cms/cms/templates/pages/page_tree.html and integreat_cms/cms/templates/language_tree/language_tree.html
 */

import { off, on } from "./utils/wrapped-events";

window.addEventListener("load", () => {
  // On the page tree, the event listeners are set after all subpages have been loaded
  if (!document.querySelector("[data-delay-event-handlers]")) {
    addDragAndDropListeners();
  }
});

/**
 * Set event listener
 */
export function addDragAndDropListeners() {
  // Only activate event listeners if explicitly enabled
  if (!document.querySelector("[data-activate-tree-drag-drop]")) return;
  console.debug("Set event handlers for tree drag & drop functionality");
  
  // event handler for starting drag events
  document.querySelectorAll(".drag").forEach((node) => {
    (node as HTMLElement).addEventListener("dragstart", dragstart);
  });
  
  // event handler for stopping drag events
  document.querySelectorAll(".drag").forEach(function (node) {
    on(node, "dragend", dragend);
  });
  
  // event handler for dragleave events
  document.querySelectorAll(".drop").forEach((node) => {
    node.addEventListener("dragleave", dragleave);
  });
  
  // event handler for drop events
  document.querySelectorAll(".drop").forEach((node) => {
    node.addEventListener("drop", (e: Event) => {
      e.preventDefault();
      drop(e as DragEvent);
    });
  });
}

/**
 * This function handles the start of a dragging event
 *
 * Manipulating the dom during dragstart event fires immediately a dragend event (chrome browser),
 * so the changes to the dom must be delayed
 */
function dragstart(event: DragEvent) {
  const target = event.target as HTMLElement;
  // prepare the dragged node id for data transfer
  event.dataTransfer.setData("text", target.getAttribute("data-drag-id"));
  window.setTimeout(() => changeDom(target));
  // get descendants of dragged node
  const descendants = JSON.parse(
      target.getAttribute("data-node-descendants")
  ) as number[];
  // add event listeners for hovering over drop regions
  document.querySelectorAll(".drop").forEach((node) => {
    // get target node id of the hovered drop region
    const drop_id = parseInt(node.getAttribute("data-drop-id"));
    if (descendants.includes(drop_id)) {
      // if the target node is a descendant of the dragged node, disallow dropping it
      on(node, "dragover", dropDisallow);
    } else {
      // else, the move would be valid and dropping is allowed
      on(node,
          "dragover",
          (e: Event) => {
            e.preventDefault();
            dropAllow(e);
          }
      );
    }
  });
}

/**
 *  manipulating the dom during dragstart event fires immediately a dragend event (chrome browser)
 * so the changes to the dom must be delayed
 *
 */
function changeDom(target: HTMLElement) {
  // change appearance of dragged item
  target.classList.remove("text-gray-800");
  target.classList.add("text-blue-500");
  // show dropping regions between table rows
  document.querySelectorAll(".drop-between").forEach((node) => {
    node.closest("tr").classList.remove("hidden");
  });
}

// These functions add the hover effect when the dragged page is hovered over a valid/invalid drop region
function dropAllow(event: Event) {
  const target = event.target as HTMLElement;
  target.parentElement.closest("tr").classList.add("drop-allow");
}
function dropDisallow(event: Event) {
  const target = event.target as HTMLElement;
  target.parentElement.closest("tr").classList.add("drop-disallow");
}

// This function handles the event that the drag stops, no matter if on a valid drop region or not
function dragend(event: Event) {
  event.preventDefault();

  const target = event.target as HTMLElement;
  // hide the drop regions between table rows
  document.querySelectorAll(".drop-between").forEach((node) => {
    node.closest("tr").classList.add("hidden");
  });
  document.querySelectorAll('.drop').forEach((node) => {
    off(node, 'dragover');
  });

  // change appearance of dragged item
  target.classList.remove("text-blue-500");
  target.classList.add("text-gray-800");
}

// This function handles the event then the cursor leaves a drop region without actually dropping
function dragleave(event: Event) {
  // remove hover effect on allowed or disallowed drop regions
  const target = (event.target as HTMLElement).closest("tr");
  target.classList.remove("drop-allow");
  target.classList.remove("drop-disallow");
}

// This function handles the event when the page is dropped onto the target div
function drop(event: DragEvent) {
  // prevent the table from collapsing again after successful drop
  document.querySelectorAll(".drag").forEach((node) => {
    off(node, "dragend");
  });
  // get dragged node id from data transfer
  var node_id = event.dataTransfer.getData("text");
  // get target node if from dropped region
  const target = (event.target as HTMLElement).closest("tr");
  const target_id = target.getAttribute("data-drop-id");
  const target_position = target.getAttribute("data-drop-position");
  // abuse confirmation dialog form to perform action
  let form = document.getElementById("confirmation-dialog").querySelector("form");
  form.action = window.location.href + node_id + "/move/" + target_id + "/" + target_position + "/";
  form.submit();
}
