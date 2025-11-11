/**
 *
 * used in:
 * poi_box.html     > contact_form.html
 *                  > event_form.html
 */

import { createIconsAt } from "./utils/create-icons";
import { getCsrfToken } from "./utils/csrf-token";

type FormResponse = { success: boolean; poi_address_container: string; poi_id: string };

const showContactFieldBox = () => {
    const contactFieldsBox = document.getElementById("contact_fields");
    contactFieldsBox?.classList.remove("hidden");
    const contactUsageBox = document.getElementById("contact_usage");
    contactUsageBox?.classList.remove("hidden");
};

const hideSearchResults = () => {
    document.getElementById("poi-query-result").classList.add("hidden");
    (document.getElementById("poi-query-input") as HTMLInputElement).value = "";
};

const renderPoiData = (poiTitle: string, newPoiData: string, poiId: string) => {
    const poiAddressContainer = document.getElementById("poi-address-container");
    if (poiAddressContainer) {
        poiAddressContainer.outerHTML = newPoiData;
    }
    document.getElementById("poi-query-input").setAttribute("placeholder", poiTitle);
    (document.getElementById("id_location") as HTMLInputElement).value = poiId;
    hideSearchResults();
    showContactFieldBox();
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
        option.getAttribute("data-poi-address"),
        option.getAttribute("data-poi-id")
    );
    document.getElementById("poi-address-container")?.classList.remove("hidden");
    console.debug("Rendered POI data");
    document.getElementById("info-location-mandatory")?.classList.add("hidden");
};

const toggleFields = () => {
    const checkbox = document.getElementById("id_has_not_location") as HTMLInputElement;
    const locationBlock = document.getElementById("location-block");
    const meetingUrlBlock = document.getElementById("meeting-url-block");
    const locationInput = document.getElementById("id_location") as HTMLInputElement;
    const onlineInput = document.getElementById("id_meeting_url") as HTMLInputElement;

    if (checkbox.checked) {
        locationBlock.classList.add("hidden");
        meetingUrlBlock.classList.remove("hidden");
    } else {
        locationBlock.classList.remove("hidden");
        meetingUrlBlock.classList.add("hidden");
    }
    locationInput.disabled = checkbox.checked;
    onlineInput.disabled = !checkbox.checked;
};

const showMessage = (response: FormResponse) => {
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
            // Handle responseData
            const responseData: FormResponse = await response.json();
            console.debug(responseData);
            showMessage(responseData);
            // If POI was created successful, show it as selected option
            if (responseData.success) {
                renderPoiData(
                    formData.get("title").toString(),
                    responseData.poi_address_container,
                    responseData.poi_id
                );
                document.getElementById("poi-address-container")?.classList.remove("hidden");
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
    // Hide the address container
    document.getElementById("poi-address-container")?.classList.add("hidden");
    // Clear the search container
    document
        .getElementById("poi-query-input")
        .setAttribute(
            "placeholder",
            document.getElementById("poi-query-input").getAttribute("data-default-placeholder")
        );
    hideSearchResults();
    // Clear the poi form
    hidePoiFormWidget();
    console.debug("Removed POI data");
    (document.getElementById("id_location") as HTMLInputElement).value = "-1";
    document.getElementById("info-location-mandatory")?.classList.remove("hidden");
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
    const checkbox = document.getElementById("id_has_not_location");

    if (document.getElementById("poi-query-input") && !document.querySelector("[data-disable-poi-query]")) {
        setPoiQueryEventListeners();
        // event handler to reset filter form
        document.getElementById("filter-reset")?.addEventListener("click", removePoi);
    }

    const contactFields = document.getElementById("contact_fields");
    contactFields?.querySelectorAll("input").forEach((el) => {
        if ((el as HTMLInputElement).value) {
            showContactFieldBox();
        }
    });

    if (checkbox) {
        checkbox.addEventListener("change", toggleFields);
        toggleFields();
    }
});
