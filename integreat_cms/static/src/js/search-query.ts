import { getCsrfToken } from "./utils/csrf-token";

window.addEventListener("load", () => {
    if (document.getElementById("table-search")) {
        setSearchQueryEventListeners();
    }
});

async function queryObjects(
    url: string,
    type: String,
    queryString: string,
    archived: boolean,
) {
    if (queryString.trim().length == 0) {
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

    if (response.status != 200) {
        return;
    }

    const data = await response.json();

    let suggestion_list = document.getElementById("table-search-suggestions");
    suggestion_list.innerHTML = "";
    suggestion_list.classList.remove("hidden");

    if (data) {
        // Set and display new data        
        for (const value of data.data) {
            let child = document.createElement("li");
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
            suggestion_list.appendChild(child);
        }
    }
}

let scheduledFunction: number | null = null;

export function setSearchQueryEventListeners() {
    console.debug("Setting search query event listeners");
    let table_search_input = document.getElementById("table-search-input") as HTMLInputElement;

    // AJAX search
    table_search_input
        .addEventListener("keyup", (event) => {
            event.preventDefault();

            // Reschedule function execution on new input
            if (scheduledFunction != null) {
                window.clearTimeout(scheduledFunction);
            }
            // Schedule function execution
            scheduledFunction = window.setTimeout(
                queryObjects,
                300,
                table_search_input.getAttribute("data-url"),
                table_search_input.getAttribute("data-object-type"),
                table_search_input.value,
                table_search_input.getAttribute("data-archived") == "true"
            );
        });

    let table_search = document.getElementById("table-search");

    table_search
        .addEventListener("focusout", (event) => {
            let search_suggestion = document.getElementById("table-search-suggestions");
            search_suggestion.classList.add("hidden");
        });

    table_search
        .addEventListener("focusin", (event) => {
            let search_suggestion = document.getElementById("table-search-suggestions");
            search_suggestion.classList.remove("hidden");
        });

    document.getElementById("table-search-suggestions").addEventListener("mousedown", ({ target }) => {
        let table_search_input = document.getElementById("table-search-input") as HTMLInputElement;
        // Don't submit a value if the user clicked e.g. on the search bar and not a specific list element
        if (!(target as HTMLElement).matches("li")) {
            return;
        }
        // Fill in search field with selected suggestion
        table_search_input.value = (target as HTMLElement).textContent;
        // Submit the search
        document.getElementById("search-submit-btn").click();
    })

    // Reset the search
    document.getElementById("search-reset-btn").addEventListener("click", (event) => {
        // Empty the search value
        table_search_input.value = "";
        // Submit the search
        document.getElementById("search-submit-btn").click();
    });
}
