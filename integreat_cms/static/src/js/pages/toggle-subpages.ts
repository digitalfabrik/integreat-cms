/*
 * The functionality to toggle subpages
 */
import { createIconsAt } from "../utils/create-icons";
import { restorePageLayout, storeExpandedState } from "./persistent_page_tree";

window.addEventListener("icon-load", () => {
    // On the page tree, the event listeners are set after all subpages have been loaded
    if (!document.querySelector("[data-delay-event-handlers]")) {
        setToggleSubpagesEventListeners();
        restorePageLayout();
    }
});

/**
 * Set all event handlers
 */
export function setToggleSubpagesEventListeners() {
    if (!document.querySelector(".toggle-subpages")) return;
    console.debug("Set event handlers for collapsing/expanding subpages");
    // event handler to hide and show subpages
    document.querySelectorAll<HTMLElement>(".toggle-subpages").forEach((element: HTMLElement) => {
        element.addEventListener("click", toggleSubpages);
        element.classList.remove("cursor-wait");
        element.classList.add("cursor-pointer", "hover:scale-125");
        element.title = element.getAttribute("data-expand-title");
    });
    // Button to expand all pages at once
    let expandAllPagesButton = document.getElementById("expand-all-pages");
    expandAllPagesButton?.addEventListener("click", expandAllPages);
    expandAllPagesButton?.classList.remove("!cursor-wait");
    expandAllPagesButton?.classList.add("hover:underline", "group");
    // Button to collapse all pages at once
    let collapseAllPagesButton = document.getElementById("collapse-all-pages");
    collapseAllPagesButton?.addEventListener("click", collapseAllPages);
    collapseAllPagesButton?.classList.remove("!cursor-wait");
    collapseAllPagesButton?.classList.add("hover:underline", "group");
}

/**
 * This function toggles all subpages of the clicked page and changes the icon
 *
 * @param event Collapse/Expand button clicked
 */
export function toggleSubpages(event: Event) {
    event.preventDefault();
    toggleSubpagesForElement((event.target as HTMLElement).closest("span"));
}

/**
 * This function toggles all subpages of the given element and changes the icon
 *
 * @param collapseSpan The page which should be toggled
 */
export function toggleSubpagesForElement(collapseSpan: HTMLSpanElement) {
    const children: number[] = JSON.parse(collapseSpan.getAttribute("data-page-children"));
    // Toggle subpages
    toggleSubpagesRecursive(children);
    // Change icon and title
    let icon = collapseSpan.querySelector("svg");
    if (icon.classList.contains("lucide-chevron-down")) {
        setExpandedState(collapseSpan, false);
    } else {
        setExpandedState(collapseSpan, true);
    }
}

/**
 * This function iterates over all direct children of a page and
 * toggles their "hidden" class if they are not yet collapsed.
 * This enables to "save" the collapsed-state of all subpages, so when showing the subpages again,
 * all previously collapsed subpages will remain collapsed.
 *
 * @param childrenIds Nodes to be toggled
 */
const toggleSubpagesRecursive = (childrenIds: Array<number>) => {
    // Foreach child: toggle class "hidden" and proceed for all children which are not explicitly hidden themselves
    childrenIds.forEach((childId) => {
        // Get child table row
        const child = document.getElementById(`page-${childId}`);
        // Hide/show table row
        child.classList.toggle("hidden");
        // Remove the left sibling from possible drop targets while it is collapsed
        document.getElementById(`page-${childId}-drop-left`)?.classList.toggle("drop-between");
        // Find out whether this page has children itself
        const collapseSpan = child.querySelector(".toggle-subpages") as HTMLElement;
        if (collapseSpan) {
            // The icon will be null if the page is a leaf node
            const icon = collapseSpan.querySelector("svg");
            if (icon.classList.contains("lucide-chevron-down")) {
                // This means the children are not yet collapsed and have to be hidden as well
                const grandChildren: number[] = JSON.parse(collapseSpan.getAttribute("data-page-children"));
                toggleSubpagesRecursive(grandChildren);
            }
        }
    });
};

/**
 * This function toggles all subpages of the clicked page and changes the icon
 *
 * @param event Collapse/Expand button clicked
 */
async function collapseAllPages() {
    (<HTMLElement[]>Array.from(document.querySelectorAll(".page-row"))).forEach((page: HTMLElement) => {
        // Hide table row of it's not a root page
        if (!page.classList.contains("level-1")) {
            page.classList.add("hidden");
        }
        // Remove the left sibling from possible drop targets
        document.getElementById(page.id + "-drop-left")?.classList.remove("drop-between");
        // Find out whether this page has children itself
        const span = page.querySelector(".toggle-subpages") as HTMLElement;
        if (span) {
            setExpandedState(span, false);
        }
    });
}

/**
 * Expand all pages
 */
const expandAllPages = async () => {
    (<HTMLElement[]>Array.from(document.querySelectorAll(".page-row"))).forEach((page: HTMLElement) => {
        // Show table row
        page.classList.remove("hidden");
        // Add the left sibling to possible drop targets
        document.getElementById(`${page.id}-drop-left`)?.classList.add("drop-between");
        // Find out whether this page has children itself
        const span = page.querySelector(".toggle-subpages") as HTMLElement;
        if (span) {
            setExpandedState(span, true);
        }
    });
}

/**
 * Sets the collapsed state for the given span element and
 * updates the icon.
 * Updates the stored collapse state, too.
 *
 * @param element The element to update
 * @param expanded whether the element should be collapsed or expanded
 */
function setExpandedState(element: HTMLElement, expanded: boolean) {
    const id: number = JSON.parse(element.getAttribute("data-page-id"));
    if (expanded) {
        element.innerHTML = '<i icon-name="chevron-down"></i>';
        element.title = element.getAttribute("data-collapse-title");
        storeExpandedState(id, true);
    } else {
        element.innerHTML = '<i icon-name="chevron-right"></i>';
        element.title = element.getAttribute("data-expand-title");
        storeExpandedState(id, false);
    }
    createIconsAt(element);
}
