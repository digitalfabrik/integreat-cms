import { createIconsAt } from "../utils/create-icons";
import { getCsrfToken } from "../utils/csrf-token";

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

const hidePoiFormWidget = () => {
    const widget = document.getElementById("poi-form-widget") as HTMLElement;
    if (widget) {
        widget.textContent = "";
    }
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

const showMessage = (response: any) => {
    const timeoutDuration = 10000;
    if (response.success) {
        hidePoiFormWidget();
        const successMessageField = document.getElementById("poi-ajax-success-message");
        successMessageField.classList.remove("hidden");
        setTimeout(() => {
            successMessageField.classList.add("hidden");
        }, timeoutDuration);
    } else {
        const errorMessageField = document.getElementById("poi-ajax-error-message");
        errorMessageField.classList.remove("hidden");
        setTimeout(() => {
            errorMessageField.classList.add("hidden");
        }, timeoutDuration);
    }
};

const showPoiFormWidget = async ({ target }: Event) => {
    const option = (target as HTMLElement).closest(".option-new-poi");
    const response = await fetch(document.getElementById("show-poi-form-button").getAttribute("data-url"));

    document.getElementById("poi-form-widget").innerHTML = await response.text();
    document.querySelector("[data-poi-title]").setAttribute("value", option.getAttribute("data-poi-title"));
    document.getElementById("show-poi-form-button").classList.add("hidden");

    // Add listeners for save and draft-save buttons
    document.querySelectorAll("[data-btn-save-poi-form]").forEach((el) => {
        el.addEventListener("click", async (event) => {
            event.preventDefault();
            const btn = event.target as HTMLInputElement;
            const form = btn.form as HTMLFormElement;
            const formData: FormData = new FormData(form);
            formData.append(btn.name, btn.value);
            if (!form.reportValidity()) {
                return;
            }
            const response = await fetch(btn.getAttribute("data-url"), {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                },
                body: formData,
            });
            // Handle messages
            const messages = await response.json();
            console.debug(messages);
            showMessage(messages);
            // If POI was created successful, show it as selected option
            if (messages.success) {
                console.debug(messages);
                renderPoiData(
                    formData.get("title").toString(),
                    messages.id,
                    formData.get("address").toString(),
                    formData.get("postcode").toString(),
                    formData.get("city").toString(),
                    formData.get("country").toString()
                );
                document.getElementById("poi-address-container")?.classList.remove("hidden");
                // Add the POI to the actual django form field
                (document.getElementById("id_location") as HTMLInputElement).value = messages.id.toString();
            }
            hidePoiFormWidget();
        });
    });
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
            showPoiFormWidget(event);
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
    // Clear the poi form
    hidePoiFormWidget();
    console.debug("Removed POI data");
};

let scheduledFunction: number | null = null;
const setPoiQueryEventListeners = () => {
    // AJAX search
    document.getElementById("poi-query-input").addEventListener("keyup", (event) => {
        hidePoiFormWidget();
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
