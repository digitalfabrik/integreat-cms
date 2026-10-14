import { createIconsAt } from "./utils/create-icons";
import { getCsrfToken } from "./utils/csrf-token";

type FormResponse = { success: boolean; place_address_container: string; place_id: string };

const showContactFieldBox = () => {
    const contactFieldsBox = document.getElementById("contact_fields");
    contactFieldsBox?.classList.remove("hidden");
    const contactUsageBox = document.getElementById("contact_usage");
    contactUsageBox?.classList.remove("hidden");
};

const hideSearchResults = () => {
    document.getElementById("place-query-result").classList.add("hidden");
    (document.getElementById("place-query-input") as HTMLInputElement).value = "";
};

const renderPlaceData = (placeTitle: string, newPlaceData: string, placeId: string) => {
    const placeAddressContainer = document.getElementById("place-address-container");
    if (placeAddressContainer) {
        placeAddressContainer.outerHTML = newPlaceData;
    }
    document.getElementById("place-query-input").setAttribute("placeholder", placeTitle);
    (document.getElementById("id_place") as HTMLInputElement).value = placeId;
    hideSearchResults();
    showContactFieldBox();
};

const hidePlaceFormWidget = () => {
    const widget = document.getElementById("place-form-widget") as HTMLElement;
    if (widget) {
        widget.textContent = "";
    }
};

const setPlace = ({ target }: Event) => {
    const option = (target as HTMLElement).closest(".option-existing-place");
    renderPlaceData(
        option.getAttribute("data-place-title"),
        option.getAttribute("data-place-address"),
        option.getAttribute("data-place-id")
    );
    document.getElementById("place-address-container")?.classList.remove("hidden");
    document.getElementById("place-query-input")?.classList.add("placeholder-gray-800", "focus:placeholder-gray-800");
    document.getElementById("place-query-input")?.classList.remove("focus:placeholder-gray-600");
    console.debug("Rendered Place data");
    document.getElementById("info-place-mandatory")?.classList.add("hidden");
};

const toggleFields = () => {
    const checkbox = document.getElementById("id_has_not_place") as HTMLInputElement;
    const placeBlock = document.getElementById("place-block");
    const meetingUrlBlock = document.getElementById("meeting-url-block");
    const placeInput = document.getElementById("id_place") as HTMLInputElement;
    const onlineInput = document.getElementById("id_meeting_url") as HTMLInputElement;

    if (checkbox.checked) {
        placeBlock.classList.add("hidden");
        meetingUrlBlock.classList.remove("hidden");
    } else {
        placeBlock.classList.remove("hidden");
        meetingUrlBlock.classList.add("hidden");
    }
    placeInput.disabled = checkbox.checked;
    onlineInput.disabled = !checkbox.checked;
};

const showMessage = (response: FormResponse) => {
    const timeoutDuration = 10000;
    if (response.success) {
        hidePlaceFormWidget();
        const successMessageField = document.getElementById("place-ajax-success-message");
        successMessageField.classList.remove("hidden");
        setTimeout(() => {
            successMessageField.classList.add("hidden");
        }, timeoutDuration);
    } else {
        const errorMessageField = document.getElementById("place-ajax-error-message");
        errorMessageField.classList.remove("hidden");
        setTimeout(() => {
            errorMessageField.classList.add("hidden");
        }, timeoutDuration);
    }
};

const showPlaceFormWidget = async ({ target }: Event) => {
    const option = (target as HTMLElement).closest(".option-new-place");
    const response = await fetch(document.getElementById("show-place-form-button").getAttribute("data-url"));

    document.getElementById("place-form-widget").innerHTML = await response.text();
    document.querySelector("[data-place-title]").setAttribute("value", option.getAttribute("data-place-title"));
    document.getElementById("show-place-form-button").classList.add("hidden");

    // Add listeners for save and draft-save buttons
    document.querySelectorAll("[data-btn-save-place-form]").forEach((el) => {
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
            // If Place was created successful, show it as selected option
            if (responseData.success) {
                renderPlaceData(
                    formData.get("title").toString(),
                    responseData.place_address_container,
                    responseData.place_id
                );
                document.getElementById("place-address-container")?.classList.remove("hidden");
            }
            hidePlaceFormWidget();
        });
    });
};

const queryPlaces = async (url: string, queryString: string, regionSlug: string, createPlaceOption: boolean) => {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            query_string: queryString,
            region_slug: regionSlug,
            create_place_option: createPlaceOption,
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
        const queryResult = document.getElementById("place-query-result");
        queryResult.classList.remove("hidden");
        queryResult.innerHTML = data;
        createIconsAt(queryResult);
    }

    document.querySelectorAll(".option-new-place").forEach((node) => {
        node.addEventListener("click", (event) => {
            event.preventDefault();
            showPlaceFormWidget(event);
        });
    });

    document.querySelectorAll(".option-existing-place").forEach((node) => {
        console.debug("Set event listener for existing Place:", node);
        node.addEventListener("click", (event) => {
            event.preventDefault();
            setPlace(event);
        });
    });

    return "";
};

const removePlace = () => {
    // Hide the address container
    document.getElementById("place-address-container")?.classList.add("hidden");
    // Clear the search container
    const placeQueryInput = document.getElementById("place-query-input");
    placeQueryInput.setAttribute("placeholder", placeQueryInput.getAttribute("data-default-placeholder"));
    placeQueryInput.classList.remove("placeholder-gray-800", "focus:placeholder-gray-800");
    placeQueryInput.classList.add("focus:placeholder-gray-600");
    hideSearchResults();
    // Clear the place form
    hidePlaceFormWidget();
    console.debug("Removed Place data");
    (document.getElementById("id_place") as HTMLInputElement).value = "-1";
    document.getElementById("info-place-mandatory")?.classList.remove("hidden");
};

let scheduledFunction: number | null = null;
const setPlaceQueryEventListeners = () => {
    // AJAX search
    document.getElementById("place-query-input").addEventListener("keyup", (event) => {
        hidePlaceFormWidget();
        event.preventDefault();
        const inputField = (event.target as HTMLElement).closest("input");

        // Reschedule function execution on new input
        if (scheduledFunction) {
            clearTimeout(scheduledFunction);
        }
        // Schedule function execution
        const timeoutDuration = 300;
        scheduledFunction = window.setTimeout(
            queryPlaces,
            timeoutDuration,
            inputField.getAttribute("data-url"),
            inputField.value,
            inputField.getAttribute("data-region-slug"),
            !inputField.classList.contains("no-new-place") // Allow suppressing the option to create a new Place
        );
    });

    // Hide AJAX search results
    document.addEventListener("click", ({ target }) => {
        if (
            !(target as HTMLElement).closest("#place-query-input") &&
            !(target as HTMLElement).closest("#place-query-result")
        ) {
            // Neither clicking on input field nor on result to select it
            document.getElementById("place-query-result").innerHTML = "";
            (document.getElementById("place-query-input") as HTMLInputElement).value = "";
        }
    });

    // Remove Place
    document.getElementById("place-remove").addEventListener("click", (event) => {
        event.preventDefault();
        removePlace();
    });
};

window.addEventListener("load", () => {
    const checkbox = document.getElementById("id_has_not_place");

    if (document.getElementById("place-query-input") && !document.querySelector("[data-disable-place-query]")) {
        setPlaceQueryEventListeners();
        // event handler to reset filter form
        document.getElementById("filter-reset")?.addEventListener("click", removePlace);
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
