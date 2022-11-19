/*
 * This file contains the dynamic handling for user organizations
 */

/**
 * Hide disallowed organization choices
 */
const updateOrganizationChoices = (event: Event) => {
    const regions = event.target as HTMLSelectElement;
    // Get all selected region ids
    const regionIds = Array.from(regions.selectedOptions).map(({ value }) => value);
    const organization = document.getElementById("id_organization") as HTMLSelectElement;
    // Hide/show the adjusted organization options
    Array.from(organization.options).forEach((element) => {
        if (element.dataset.regionId) {
            if (regionIds.includes(element.dataset.regionId)) {
                element.classList.remove("hidden");
            } else {
                element.classList.add("hidden");
                /* eslint-disable-next-line no-param-reassign */
                element.selected = false;
            }
        }
    });
};

window.addEventListener("load", () => {
    const regions = document.getElementById("id_regions");
    regions?.addEventListener("change", updateOrganizationChoices);
    // Simulate initial input after page load
    regions?.dispatchEvent(new Event("change"));
});
