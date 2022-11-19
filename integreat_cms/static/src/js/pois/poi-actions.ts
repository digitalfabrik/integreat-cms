import { getCsrfToken } from "../utils/csrf-token";

export const updateField = (fieldName: string, value: string) => {
    const field = document.getElementById(`id_${fieldName}`) as HTMLInputElement;
    // Only fill value if it was changed
    if (value && field.value !== value) {
        field.value = value;
        field.classList.add("!border-green-500");
        // Reset green border after 5 seconds
        const timeoutDuration = 5000;
        setTimeout(() => {
            field.classList.remove("!border-green-500");
        }, timeoutDuration);
    }
};

const autoCompleteAddress = async () => {
    const street = (document.getElementById("id_address") as HTMLInputElement).value;
    const postcode = (document.getElementById("id_postcode") as HTMLInputElement).value;
    const city = (document.getElementById("id_city") as HTMLInputElement).value;

    // Only try auto filling if street and either postcode or city are given
    if (street.trim().length === 0 || (postcode.trim().length === 0 && city.trim().length === 0)) {
        return;
    }

    const autoFillCoordinates = document.getElementById("auto-fill-coordinates") as HTMLInputElement;
    const error = document.getElementById("nominatim-error");
    error.classList.add("hidden");

    const response = await fetch(autoFillCoordinates.dataset.url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            street,
            postcode,
            city,
        }),
    });

    const data = await response.json();

    const HTTP_STATUS_OK = 200;
    if (response.status !== HTTP_STATUS_OK) {
        error.textContent = data.error;
        error.classList.remove("hidden");
        return;
    }

    updateField("postcode", data.postcode);
    updateField("city", data.city);
    updateField("country", data.country);

    if (autoFillCoordinates.checked) {
        updateField("longitude", data.longitude);
        updateField("latitude", data.latitude);
    }

    const longitude = document.getElementById("id_longitude") as HTMLInputElement;
    const latitude = document.getElementById("id_latitude") as HTMLInputElement;

    longitude.dispatchEvent(new Event("focusout"));
    latitude.dispatchEvent(new Event("focusout"));
};

const toggleOpeningHoursWidget = (temporarilyClosed: HTMLInputElement) => {
    const openingHoursWidget = document.querySelector("opening-hours-widget");
    if (temporarilyClosed.checked) {
        openingHoursWidget.classList.add("hidden");
    } else {
        openingHoursWidget.classList.remove("hidden");
    }
};

window.addEventListener("load", () => {
    document.getElementById("id_address")?.addEventListener("focusout", autoCompleteAddress);
    document.getElementById("id_postcode")?.addEventListener("focusout", autoCompleteAddress);
    document.getElementById("id_city")?.addEventListener("focusout", autoCompleteAddress);

    const longitude = document.getElementById("id_longitude") as HTMLInputElement;
    const latitude = document.getElementById("id_latitude") as HTMLInputElement;

    document.getElementById("auto-fill-coordinates")?.addEventListener("input", ({ target }) => {
        if ((target as HTMLInputElement).checked) {
            autoCompleteAddress();
        } else {
            // Reset to initial value
            longitude.value = longitude.dataset.initial;
            latitude.value = latitude.dataset.initial;

            longitude.dispatchEvent(new Event("focusout"));
            latitude.dispatchEvent(new Event("focusout"));
        }
    });

    // Add possibility to reset coordinates to initial values
    if (longitude?.value) {
        // If the initial value was set, always restore this one
        longitude.dataset.initial = longitude.value;
    } else {
        // Else, restore the last manual input
        longitude?.addEventListener("focusout", () => {
            longitude.dataset.initial = longitude.value;
        });
    }
    if (latitude?.value) {
        latitude.dataset.initial = latitude.value;
    } else {
        latitude?.addEventListener("focusout", () => {
            latitude.dataset.initial = latitude.value;
        });
    }

    // Hide opening hours if temporarily closed
    const temporarilyClosed = document.getElementById("id_temporarily_closed") as HTMLInputElement;
    if (temporarilyClosed) {
        toggleOpeningHoursWidget(temporarilyClosed);
        temporarilyClosed.addEventListener("click", () => toggleOpeningHoursWidget(temporarilyClosed));
    }
});
