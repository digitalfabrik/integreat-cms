import { getCsrfToken } from "./utils/csrf-token";

const queryObjects = async (url: string, type: string, queryString: string, archived: boolean) => {
    if (queryString.trim().length === 0) {
        document.getElementById("table-search-suggestions").classList.add("hidden");
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

    const suggestionList = document.getElementById("table-search-suggestions");
    suggestionList.innerHTML = "";
    suggestionList.classList.remove("hidden");

    if (data) {
        // Set and display new data
        for (const value of data.data) {
            const child = document.createElement("li");
            child.classList.add(
                "inline-block",
                "whitespace-nowrap",
                "px-4",
                "py-3",
                "text-gray-800",
                "hover:bg-gray-300",
                "bg-gray-200",
                "w-full",
                "overflow-x-hidden",
                "text-ellipsis",
                "align-top"
            );
            child.innerText = value.title;
            suggestionList.appendChild(child);
        }
    }
};

let scheduledFunction: number | null = null;

export const setSearchQueryEventListeners = () => {
    console.debug("Setting search query event listeners");
    const tableSearchInput = document.getElementById("table-search-input") as HTMLInputElement;

    // AJAX search
    tableSearchInput.addEventListener("keyup", (event) => {
        event.preventDefault();

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
            tableSearchInput.getAttribute("data-archived") === "true"
        );
    });

    const tableSearch = document.getElementById("table-search");

    tableSearch.addEventListener("focusout", (_event) => {
        const searchSuggestion = document.getElementById("table-search-suggestions");
        searchSuggestion.classList.add("hidden");
    });

    tableSearch.addEventListener("focusin", (_event) => {
        const searchSuggestion = document.getElementById("table-search-suggestions");
        searchSuggestion.classList.remove("hidden");
    });

    document.getElementById("table-search-suggestions").addEventListener("mousedown", ({ target }) => {
        const tableSearchInput = document.getElementById("table-search-input") as HTMLInputElement;
        // Don't submit a value if the user clicked e.g. on the search bar and not a specific list element
        if (!(target as HTMLElement).matches("li")) {
            return;
        }
        // Fill in search field with selected suggestion
        tableSearchInput.value = (target as HTMLElement).textContent;
        // Submit the search
        document.getElementById("search-submit-btn").click();
    });

    // Reset the search
    document.getElementById("search-reset-btn")?.addEventListener("click", (_event) => {
        // Empty the search value
        tableSearchInput.value = "";
        // Submit the search
        document.getElementById("search-submit-btn").click();
    });
};

window.addEventListener("load", () => {
    if (document.getElementById("table-search")) {
        setSearchQueryEventListeners();
    }
});
