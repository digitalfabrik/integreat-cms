import feather from "feather-icons";
import { off, on } from "../utils/wrapped-events";

let initialPageTitle: string;
window.addEventListener("change", () => {
  // Event handler for changing the parent page option
  const parentEl = document.getElementById("parent");
  if (parentEl) {
    parentEl.addEventListener("change", getPageOrderTable);
  }

  // Event handler for updating the page title
  const pageTitleEl = document.getElementById("id_title") as HTMLInputElement;
  if (pageTitleEl) {
    pageTitleEl.addEventListener("input", updatePageTitle);
    // save initial page title
    initialPageTitle = pageTitleEl.value;
  }

  // Register all handlers once initially
  registerEventHandlers();
});

// This function updates the page order table each time the parent select changes
async function getPageOrderTable({ target }: Event) {
  // Get selected option node
  const selectedOption = document
    .getElementById("parent")
    .querySelector(
      'option[value="' + (target as HTMLInputElement).value + '"]'
    );
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
    const pageContainedInSiblings = document
      .querySelector(".drag")
      .getAttribute("data-contained-in-siblings");
    if (pageContainedInSiblings) {
      // Reset hidden field values to default value
      document
        .getElementById("id_related_page")
        .setAttribute(
          "value",
          (document.getElementById("id_related_page") as HTMLInputElement)
            .defaultValue
        );
      document
        .getElementById("id_position")
        .setAttribute(
          "value",
          (document.getElementById("id_position") as HTMLInputElement)
            .defaultValue
        );
    } else {
      // Change hidden field values to last child of parent
      document
        .getElementById("id_related_page")
        .setAttribute("value", (target as HTMLInputElement).value);
      document
        .getElementById("id_position")
        .setAttribute("value", "last-child");
    }
    // Update the modified page title
    updatePageTitle();
    // Trigger icon replacement
    feather.replace();
    // Register event handlers
    registerEventHandlers();
  } catch (error) {
    // Show error message instead of table
    document.getElementById("page_order_table").innerHTML =
      '<div class="bg-red-100 border-l-4 border-red-500 text-red-500 px-4 py-3 my-4" role="alert"><p>' +
      error.message +
      "</p></div>";
  }
}

// This function inserts the updated page title in the page order table
function updatePageTitle() {
  let pageTitle = (document.getElementById("id_title") as HTMLInputElement)
    .value;
  if (pageTitle == "" || pageTitle == initialPageTitle) {
    pageTitle = document
      .getElementById("page_title")
      .getAttribute("data-default-title");
  }
  document.getElementById("page_title").innerText = pageTitle;
}

// Function for registering all event handlers for drag/drop events
function registerEventHandlers() {
  // At first, reset all existing handlers
  document.querySelectorAll(".drop").forEach((node) => {
    off(node, ["dragleave", "dragover", "drop"]);
  });
  // Event handlers for drag events (delay because of behaviour in Chrome browser)
  document.querySelectorAll(".drag").forEach((node) =>
    on(node, "dragstart", (event) => {
      window.setTimeout(() => dragstart(event));
    })
  );

  document.querySelectorAll(".drag").forEach((el) => {
    on(el, "dragend", (event) => {
      event.preventDefault();
      dragend(event);
    });
  });

  // Event handlers for drop events
  document.querySelectorAll(".drop").forEach((node) => {
    on(node, "dragover", (event) => {
      event.preventDefault();
      dragover(event);
    });
    on(node, "dragleave", (event) => {
      event.preventDefault();
      dragleave(event);
    });
    on(node, "drop", (event) => {
      event.preventDefault();
      drop(event);
    });
  });
}

/*
 * This function handles the start of a dragging event
 *
 * Manipulating the dom during dragstart event fires immediately a dragend event (chrome browser),
 * so the changes to the dom must be delayed
 */
function dragstart({ target }: Event) {
  // change appearance of dragged item
  (target as HTMLElement).classList.remove("text-gray-800");
  (target as HTMLElement).classList.add("text-blue-500");
  // show dropping regions between table rows
  document.querySelectorAll(".drop-between").forEach((node) => {
    node.closest("tr").classList.remove("hidden");
  });
}

// This function adds the hover effect when the dragged page is hovered over a valid drop region
function dragover({ target }: Event) {
  (target as HTMLElement).parentElement
    .closest("tr")
    .classList.add("drop-allow");
}

// This function handles the event that the drag stops, no matter if on a valid drop region or not
function dragend({ target }: Event) {
  // Hide the drop regions between table rows
  document.querySelectorAll(".drop-between").forEach((node) => {
    node.closest("tr").classList.add("hidden");
  });
  // Change appearance of dragged item
  (target as HTMLElement).classList.remove("text-blue-500");
  (target as HTMLElement).classList.add("text-gray-800");
}

// This function handles the event then the cursor leaves a drop region without actually dropping
function dragleave(event: Event) {
  // Remove hover effect on allowed or disallowed drop regions
  const target = (event.target as HTMLElement).parentElement.closest("tr");
  target.classList.remove("drop-allow");
}

// This function handles the event when the page is dropped onto the target div
function drop(event: Event) {
  // Get the table row which was dragged
  let draggedPage = document.querySelector(".drag").closest("tr");
  // Get the table row onto which the page was dropped
  let target = (event.target as HTMLElement).parentElement.closest("tr");
  // Insert the page before the drop target
  target.before(draggedPage);

  // Toggle classes to deactivate the drop region where the dragged page was dropped
  [
    "drop",
    "drop-deactivated",
    "drop-between",
    "drop-between-deactivated",
  ].forEach((cls) => target.classList.toggle(cls));
  // Remove the drop-allow class which creates the hover effect (blue line)
  target.classList.remove("drop-allow");
  // Toggle classes to activate the previously deactivated drop regions
  document
    .querySelectorAll(".drop-deactivated")
    .forEach(
      (node) =>
        node.classList.toggle("drop") &&
        node.classList.toggle("drop-deactivated")
    );

  document
    .querySelectorAll(".drop-between-deactivated")
    .forEach(
      (node) =>
        node.classList.toggle("drop-between") &&
        node.classList.toggle("drop-between-deactivated")
    );

  // Passing the values to the hidden fields
  document
    .getElementById("id_related_page")
    .setAttribute("value", target.getAttribute("data-drop-id"));
  document
    .getElementById("id_position")
    .setAttribute("value", target.getAttribute("data-drop-position"));
  // Register new event handlers
  registerEventHandlers();
}
