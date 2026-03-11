/*
 * This file contains functions for country flag fields in the language form
 */

window.addEventListener("load", () => {
    // Get all country flag fields
    Array.from(document.getElementsByClassName("country-flag-field")).forEach((element: Element) => {
        // Add event listener for change events
        element.addEventListener("change", ({ target }) => {
            const countryFlagField = target as HTMLInputElement;
            const countryFlag = countryFlagField.parentNode.parentNode.querySelector(".country-flag");
            // Check whether a country was selected
            if (countryFlagField.value) {
                // Remove previous flag
                /* eslint-disable-next-line prefer-spread */
                countryFlag.classList.remove.apply(
                    countryFlag.classList,
                    Array.from(countryFlag.classList).filter((v) => v.startsWith("fp-"))
                );
                // Add new flag
                countryFlag.classList.add(`fp-${countryFlagField.value}`);
                // Show flag in case it was hidden before
                countryFlag.classList.remove("hidden");
                // Remove left rounded borders
                countryFlagField.classList.remove("rounded-l");
                countryFlagField.classList.remove("border-l");
            } else {
                // Hide previous flag
                countryFlag.classList.add("hidden");
                // Add left rounded borders
                countryFlagField.classList.add("rounded-l");
                countryFlagField.classList.add("border-l");
            }
        });
    });
});
