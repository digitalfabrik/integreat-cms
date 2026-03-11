/*
 * This file contains the dynamic handling for user roles
 */

const updateRoleField = (staffCheckbox: HTMLInputElement) => {
    const userRoles = document.getElementById("id_role") as HTMLInputElement;
    const userStaffRoles = document.getElementById("id_staff_role") as HTMLInputElement;
    const userOrganization = document.getElementById("id_organization") as HTMLInputElement;
    userRoles.required = !staffCheckbox.checked;
    userStaffRoles.required = staffCheckbox.checked;
    // Show/hide all elements which are just meant for (non-)staff users
    const showForStaff = Array.from(document.getElementsByClassName("show-for-staff"));
    const showForNonStaff = Array.from(document.getElementsByClassName("show-for-non-staff"));
    if (staffCheckbox.checked) {
        showForNonStaff.forEach((element) => element.classList.add("hidden"));
        showForStaff.forEach((element) => element.classList.remove("hidden"));
        userRoles.value = "";
        userOrganization.value = "";
    } else {
        showForStaff.forEach((element) => element.classList.add("hidden"));
        showForNonStaff.forEach((element) => element.classList.remove("hidden"));
        userStaffRoles.value = "";
    }
};

const updateRegionField = (staffCheckbox: HTMLInputElement, superuserCheckbox: HTMLInputElement) => {
    const regionField = document.getElementById("id_regions") as HTMLInputElement;
    regionField.required = !staffCheckbox.checked && !superuserCheckbox?.checked;
};

window.addEventListener("load", () => {
    const superuserCheckbox = document.getElementById("id_is_superuser") as HTMLInputElement;
    const staffCheckbox = document.getElementById("id_is_staff") as HTMLInputElement;
    if (staffCheckbox) {
        updateRoleField(staffCheckbox);
        updateRegionField(staffCheckbox, superuserCheckbox);
        // Toggle roles selection according to staff status
        staffCheckbox.addEventListener("change", () => {
            // Deactivate superuser as well when user is not staff
            if (!staffCheckbox.checked) {
                superuserCheckbox.checked = false;
            }
            updateRoleField(staffCheckbox);
            updateRegionField(staffCheckbox, superuserCheckbox);
        });
        // Activate staff as well when user is super admin
        superuserCheckbox?.addEventListener("change", () => {
            if (superuserCheckbox.checked && !staffCheckbox.checked) {
                staffCheckbox.checked = true;
                updateRoleField(staffCheckbox);
            }
            updateRegionField(staffCheckbox, superuserCheckbox);
        });
    }
});
