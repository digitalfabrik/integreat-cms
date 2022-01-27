import feather from "feather-icons";

/*
 * The functionality to toggle subpages
 */

window.addEventListener("load", () => {
  // event handler to hide and show subpages
  document
    .querySelectorAll(".collapse-subpages")
    .forEach((el) => el.addEventListener("click", toggleSubpages));
});

/*
 * This function toggles all subpages of the clicked page and changes the icon
 */
function toggleSubpages(event: Event) {
  event.preventDefault();
  // Get span with all data options
  const collapseSpan = (event.target as HTMLElement).closest("span");
  // Toggle subpages
  toggleSubpagesRecursive(collapseSpan);
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

/*
 * This function iterates over all direct children of a page and
 * toggles their "hidden" class if they are not yet collapsed.
 * This enables to "save" the collapsed-state of all subpages, so when showing the subpages again,
 * all previously collapsed subpages will remain collapsed.
 */
function toggleSubpagesRecursive(collapseSpan: HTMLElement) {
  // Get children of page
  const children: number[] = JSON.parse(
    collapseSpan.getAttribute("data-page-children")
  );
  // Foreach child: toggle class "hidden" and proceed for all children which are not explicitly hidden themselves
  children.forEach((childId) => {
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
        toggleSubpagesRecursive(collapseSpan);
      }
    }
  });
}
