import { createIconsAt } from "../utils/create-icons";
import { off, on } from "../utils/wrapped-events";

let initialPageTitle: string;

// This function inserts the updated page title in the page order table
const updatePageTitle = () => {
    let pageTitle = (document.getElementById("id_title") as HTMLInputElement).value;
    if (pageTitle === "" || pageTitle === initialPageTitle) {
        pageTitle = document.getElementById("page_title").getAttribute("data-default-title");
    }
    document.getElementById("page_title").innerText = pageTitle;
};

/*
 * This function handles the start of a dragging event
 *
 * Manipulating the dom during dragstart event fires immediately a dragend event (chrome browser),
 * so the changes to the dom must be delayed
 */
const dragstart = ({ target }: Event) => {
    // change appearance of dragged item
    (target as HTMLElement).classList.remove("text-gray-800");
    (target as HTMLElement).classList.add("text-blue-500");
    // show dropping regions between table rows
    document.querySelectorAll(".drop-between").forEach((node) => {
        node.closest("tr").classList.remove("hidden");
    });
};

// This function adds the hover effect when the dragged page is hovered over a valid drop region
const dragover = ({ target }: Event) => {
    (target as HTMLElement).parentElement.closest("tr").classList.add("drop-allow");
};

// This function handles the event that the drag stops, no matter if on a valid drop region or not
const dragend = ({ target }: Event) => {
    // Hide the drop regions between table rows
    document.querySelectorAll(".drop-between").forEach((node) => {
        node.closest("tr").classList.add("hidden");
    });
    // Change appearance of dragged item
    (target as HTMLElement).classList.remove("text-blue-500");
    (target as HTMLElement).classList.add("text-gray-800");
};

// This function handles the event then the cursor leaves a drop region without actually dropping
const dragleave = (event: Event) => {
    // Remove hover effect on allowed or disallowed drop regions
    const target = (event.target as HTMLElement).parentElement.closest("tr");
    target.classList.remove("drop-allow");
};

// This function handles the event when the page is dropped onto the target div
const drop = (event: Event) => {
    // Get the table row which was dragged
    const draggedPage = document.querySelector(".drag").closest("tr");
    // Get the table row onto which the page was dropped
    const target = (event.target as HTMLElement).parentElement.closest("tr");
    // Insert the page before the drop target
    target.before(draggedPage);

    // Toggle classes to deactivate the drop region where the dragged page was dropped
    ["drop", "drop-deactivated", "drop-between", "drop-between-deactivated"].forEach((cls) =>
        target.classList.toggle(cls)
    );
    // Remove the drop-allow class which creates the hover effect (blue line)
    target.classList.remove("drop-allow");
    // Toggle classes to activate the previously deactivated drop regions
    document
        .querySelectorAll(".drop-deactivated")
        .forEach((node) => node.classList.toggle("drop") && node.classList.toggle("drop-deactivated"));

    document
        .querySelectorAll(".drop-between-deactivated")
        .forEach((node) => node.classList.toggle("drop-between") && node.classList.toggle("drop-between-deactivated"));

    // Passing the values to the hidden fields
    document.getElementById("id__ref_node_id").setAttribute("value", target.getAttribute("data-drop-id"));
    document.getElementById("id__position").setAttribute("value", target.getAttribute("data-drop-position"));
    // Register new event handlers
    /* eslint-disable-next-line @typescript-eslint/no-use-before-define */
    registerEventHandlers();
};

// Function for registering all event handlers for drag/drop events
const registerEventHandlers = () => {
    // At first, reset all existing handlers
    document.querySelectorAll(".drop").forEach((node) => {
        off(node, ["dragleave", "dragover", "drop"]);
    });
    // Event handlers for drag events (delay because of behaviour in Chrome browser)
    document.querySelectorAll(".drag").forEach((node) =>
        on(node, "dragstart", (event: Event) => {
            window.setTimeout(() => dragstart(event));
        })
    );

    document.querySelectorAll(".drag").forEach((el) => {
        on(el, "dragend", (event: Event) => {
            event.preventDefault();
            dragend(event);
        });
    });

    // Event handlers for drop events
    document.querySelectorAll(".drop").forEach((node) => {
        on(node, "dragover", (event: Event) => {
            event.preventDefault();
            dragover(event);
        });
        on(node, "dragleave", (event: Event) => {
            event.preventDefault();
            dragleave(event);
        });
        on(node, "drop", (event: Event) => {
            event.preventDefault();
            drop(event);
        });
    });
};

const escapeMeta = (raw: any) => {
    if (typeof raw !== "string") {
        return "";
    }
    return raw.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
};

// This function updates the page order table each time the parent select changes
const getPageOrderTable = async ({ target }: Event) => {
    const parentField = target as HTMLInputElement;
    // Get selected option node
    const selectedOption = document.getElementById("parent").querySelector(`option[value="${parentField.value}"]`);
    // Fetch page order table
    try {
        const response = await fetch(selectedOption.getAttribute("data-url"));
        if (!response.ok) {
            throw new Error(response.statusText);
        }
        const html = await response.text();
        // Load new page order table
        document.getElementById("page_order_table").innerHTML = html;
        // Check if the page is part of the parent's children
        const pageContainedInSiblings = document.querySelector(".drag").getAttribute("data-contained-in-siblings");
        const lastSiblingId = escapeMeta(document.getElementById("last-sibling")?.getAttribute("data-drop-id"));
        const refNodeField = document.getElementById("id__ref_node_id") as HTMLInputElement;
        const positionField = document.getElementById("id__position") as HTMLInputElement;
        // Save initial value for resetting the page order table later if initial parent is re-selected
        if (!refNodeField.hasAttribute("data-default-value")) {
            refNodeField.setAttribute("data-default-value", escapeMeta(refNodeField.value));
        }
        if (!positionField.hasAttribute("data-default-value")) {
            positionField.setAttribute("data-default-value", escapeMeta(positionField.value));
        }
        if (pageContainedInSiblings) {
            // Reset hidden field values to default value
            refNodeField.value = escapeMeta(refNodeField.getAttribute("data-default-value"));
            positionField.value = escapeMeta(positionField.getAttribute("data-default-value"));
        } else if (lastSiblingId) {
            // Change hidden field values to right of last sibling
            refNodeField.value = lastSiblingId;
            positionField.value = "right";
        } else {
            // Change hidden field values to first child of parent
            refNodeField.value = escapeMeta(parentField.value);
            positionField.value = "first-child";
        }
        // Update the modified page title
        updatePageTitle();
        // Trigger icon replacement
        createIconsAt(document.getElementById("page_order_table"));
        // Register event handlers
        registerEventHandlers();
    } catch (error: any) {
        // Show error message instead of table
        document.getElementById("page_order_table").innerHTML =
            `<div class="bg-red-100 border-l-4 border-red-500 text-red-700 px-4 py-3 my-4" role="alert"><p>${escapeMeta(
                error.message
            )}</p></div>`;
    }
};

window.addEventListener("load", () => {
    // Only activate event listeners if explicitly enabled
    if (!document.querySelector("[data-activate-page-order]")) {
        return;
    }

    // Event handler for changing the parent page option
    const parentEl = document.getElementById("parent");
    parentEl.addEventListener("change", getPageOrderTable);

    // Event handler for updating the page title
    const pageTitleEl = document.getElementById("id_title") as HTMLInputElement;
    pageTitleEl.addEventListener("input", updatePageTitle);
    // save initial page title
    initialPageTitle = pageTitleEl.value;

    // Register all handlers once initially
    registerEventHandlers();
});
