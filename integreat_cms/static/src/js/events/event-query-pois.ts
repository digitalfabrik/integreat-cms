import { createIconsAt } from "../utils/create-icons";
import { getCsrfToken } from "../utils/csrf-token";

const newPoiWindow = ({ target }: Event) => {
    const option = (target as HTMLElement).closest(".option-new-poi");
    const newWindow = window.open(option.getAttribute("data-url"), "_blank");
    newWindow.onload = () => {
        newWindow.document.getElementById("id_title").setAttribute("value", option.getAttribute("data-poi-title"));
    };
};

const renderPoiData = (
    queryPlaceholder: string,
    id: string,
    address: string,
    postcode: string,
    city: string,
    country: string
) => {
    document.getElementById("poi-query-input").setAttribute("placeholder", queryPlaceholder);
    document.getElementById("id_location")?.setAttribute("value", id);
    const poiAddress = document.getElementById("poi-address");
    if (poiAddress) {
        poiAddress.textContent = `${address}\n${postcode} ${city}\n${country}`;
    }
    document
        .getElementById("poi-google-maps-link")
        ?.setAttribute(
            "href",
            `https://www.google.com/maps/search/?api=1&query=${address}, ${postcode} ${city}, ${country}`
        );
    document.getElementById("poi-query-result").classList.add("hidden");
    (document.getElementById("poi-query-input") as HTMLInputElement).value = "";
};

const setPoi = ({ target }: Event) => {
    const option = (target as HTMLElement).closest(".option-existing-poi");
    renderPoiData(
        option.getAttribute("data-poi-title"),
        option.getAttribute("data-poi-id"),
        option.getAttribute("data-poi-address"),
        option.getAttribute("data-poi-postcode"),
        option.getAttribute("data-poi-city"),
        option.getAttribute("data-poi-country")
    );
    // Show the address container
    document.getElementById("poi-address-container")?.classList.remove("hidden");
    console.debug("Rendered POI data");
};

const queryPois = async (url: string, queryString: string, regionSlug: string, createPoiOption: boolean) => {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            query_string: queryString,
            region_slug: regionSlug,
            create_poi_option: createPoiOption,
        }),
    });

    const HTTP_STATUS_OK = 200;
    if (response.status !== HTTP_STATUS_OK) {
        // Invalid status => return empty result
        return "";
    }

    const data = await response.text();

    if (data) {
        // Set and display new data
        const queryResult = document.getElementById("poi-query-result");
        queryResult.classList.remove("hidden");
        queryResult.innerHTML = data;
        createIconsAt(queryResult);
    }

    document.querySelectorAll(".option-new-poi").forEach((node) => {
        node.addEventListener("click", (event) => {
            event.preventDefault();
            newPoiWindow(event);
        });
    });

    document.querySelectorAll(".option-existing-poi").forEach((node) => {
        console.debug("Set event listener for existing POI:", node);
        node.addEventListener("click", (event) => {
            event.preventDefault();
            setPoi(event);
        });
    });

    return "";
};

const removePoi = () => {
    renderPoiData(
        document.getElementById("poi-query-input").getAttribute("data-default-placeholder"),
        "-1",
        "",
        "",
        "",
        ""
    );
    // Hide the address container
    document.getElementById("poi-address-container")?.classList.add("hidden");
    console.debug("Removed POI data");
};

let scheduledFunction: number | null = null;
const setPoiQueryEventListeners = () => {
    // AJAX search
    document.getElementById("poi-query-input").addEventListener("keyup", (event) => {
        event.preventDefault();
        const inputField = (event.target as HTMLElement).closest("input");

        // Reschedule function execution on new input
        if (scheduledFunction) {
            clearTimeout(scheduledFunction);
        }
        // Schedule function execution
        const timeoutDuration = 300;
        scheduledFunction = window.setTimeout(
            queryPois,
            timeoutDuration,
            inputField.getAttribute("data-url"),
            inputField.value,
            inputField.getAttribute("data-region-slug"),
            !inputField.classList.contains("no-new-poi") // Allow suppressing the option to create a new POI
        );
    });

    // Hide AJAX search results
    document.addEventListener("click", ({ target }) => {
        if (
            !(target as HTMLElement).closest("#poi-query-input") &&
            !(target as HTMLElement).closest("#poi-query-result")
        ) {
            // Neither clicking on input field nor on result to select it
            document.getElementById("poi-query-result").innerHTML = "";
            (document.getElementById("poi-query-input") as HTMLInputElement).value = "";
        }
    });

    // Remove POI
    document.getElementById("poi-remove").addEventListener("click", (event) => {
        event.preventDefault();
        removePoi();
    });
};

window.addEventListener("load", () => {
    if (document.getElementById("poi-query-input") && !document.querySelector("[data-disable-poi-query]")) {
        setPoiQueryEventListeners();
        // event handler to reset filter form
        document.getElementById("filter-reset")?.addEventListener("click", removePoi);
    }
});
