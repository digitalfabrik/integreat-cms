/**
 * 
 * Module to provide DOM Manipulation functionality
 * 
 * used in the template _search_input.html
 * 
 * module's attribute: "data-js-<moduleName>"
 * 
 * @module search-query
 * 
 */

/**
 * The moduleName used to construct the module's attribute
 */
export const moduleName = "search-query"

import { getCsrfToken } from "./utils/csrf-token";

const queryObjects = async (url: string, type: string, queryString: string, archived: boolean, root: HTMLElement) => {
    if (queryString.trim().length === 0) {
        root.querySelector("#table-search-suggestions").classList.add("hidden");
        return;
    }

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            query_string: queryString,
            object_types: [type],
            archived,
        }),
    });

    const HTTP_STATUS_OK = 200;
    if (response.status !== HTTP_STATUS_OK) {
        return;
    }

    const data = await response.json();

    const suggestionList = root.querySelector("#table-search-suggestions");
    suggestionList.innerHTML = "";
    suggestionList.classList.remove("hidden");

    if (data) {
        // Set and display new data
        data.data.forEach((value: any, index: number) => {
            const child = document.createElement("li");
            child.classList.add(
                "inline-block",
                "whitespace-nowrap",
                "my-0.5",
                "px-4",
                "py-3",
                "text-gray-800",
                "focus:ring-2",
                "hover:bg-gray-300",
                "w-full",
                "overflow-x-hidden",
                "text-ellipsis",
                "align-top"
            );
            child.setAttribute("role", "option");
            child.setAttribute("id", `suggestion-${index}`);
            child.setAttribute("tabindex", "0");
            child.innerText = value.title;
            suggestionList.appendChild(child);
        });
    }
};

let scheduledFunction: number | null = null;
let focusedIndex = -1;

export const setSearchQueryEventListeners = (root:HTMLElement) => {
    console.debug("Setting search query event listeners");
    const resetButton = root.querySelector("#search-reset-btn");
    const suggestionList = root.querySelector("#table-search-suggestions") as HTMLInputElement;
    const tableSearchInput = root.querySelector("#table-search-input") as HTMLInputElement;

    // AJAX search
    tableSearchInput.addEventListener("keyup", (event) => {
        // Ignore navigation keys for API calls
        if (["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight", "Escape", "Tab"].includes(event.key)) {
            return;
        }

        // Reschedule function execution on new input
        if (scheduledFunction != null) {
            window.clearTimeout(scheduledFunction);
        }
        // Schedule function execution
        const timeoutDuration = 300;
        scheduledFunction = window.setTimeout(
            queryObjects,
            timeoutDuration,
            tableSearchInput.getAttribute("data-url"),
            tableSearchInput.getAttribute("data-object-type"),
            tableSearchInput.value,
            tableSearchInput.getAttribute("data-archived") === "true",
            root
        );
    });

    tableSearchInput.addEventListener("keydown", (event) => {
        const suggestions = Array.from(suggestionList?.children || []) as HTMLElement[];

        if (suggestions.length === 0) {
            return;
        }

        if (event.key === "ArrowDown") {
            event.preventDefault();
            focusedIndex = (focusedIndex + 1) % suggestions.length;
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            focusedIndex = (focusedIndex - 1 + suggestions.length) % suggestions.length;
        } else if (event.key === "Enter") {
            const target = event.target as HTMLElement;
            const activeSuggestion = suggestions[focusedIndex];
            if (activeSuggestion || target.matches("li")) {
                tableSearchInput.value = activeSuggestion.textContent || target.textContent;
                root.querySelector<HTMLButtonElement>("#search-submit-btn")?.click();
            }
            return;
        } else if (event.key === "Escape") {
            suggestionList?.classList.add("hidden");
            focusedIndex = -1;
            return;
        }

        suggestions.forEach((child, index) => {
            if (index === focusedIndex) {
                child.setAttribute("aria-selected", "true");
                child.classList.add("bg-gray-300");
            } else {
                child.setAttribute("aria-selected", "false");
                child.classList.remove("bg-gray-300");
            }
        });
    });

    suggestionList?.addEventListener("keydown", (event: KeyboardEvent) => {
        if (event.key === "Enter") {
            const activeSuggestion = document.activeElement as HTMLElement;
            if (activeSuggestion && suggestionList.contains(activeSuggestion)) {
                event.preventDefault();
                tableSearchInput.value = activeSuggestion.textContent || "";
                root.querySelector<HTMLButtonElement>("#search-submit-btn")?.click();
                suggestionList?.classList.add("hidden");
            }
        }
    });

    suggestionList?.addEventListener("mousedown", (event) => {
        const target = event.target as HTMLElement;
        if (target.matches("li")) {
            // Fill in search field with selected suggestion
            tableSearchInput.value = target.textContent || "";
            root.querySelector<HTMLButtonElement>("#search-submit-btn")?.click();
        }
    });

    tableSearchInput.addEventListener("focus", (_event) => {
        suggestionList.classList.remove("hidden");
    });

    tableSearchInput.addEventListener("blur", (_event) => {
        suggestionList.classList.remove("hidden");
    });

    resetButton?.addEventListener("click", () => {
        tableSearchInput.value = "";
        root.querySelector<HTMLButtonElement>("#search-submit-btn").click();
        focusedIndex = -1;
    });
};

export default function init(root:HTMLElement) {
    setSearchQueryEventListeners(root)
}

